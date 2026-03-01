from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_integracao import (
    IntegracaoCreate,
    IntegracaoListResponse,
    IntegracaoResponse,
    IntegracaoTesteRequest,
    IntegracaoTesteResponse,
    IntegracaoUpdate,
)
from yumi.services import integracao_service

router = APIRouter()

# =====================================================
# POST - Criar integração
# =====================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=IntegracaoResponse,
    summary="Criar nova integração"
)
async def criar_integracao(
    integracao_data: IntegracaoCreate,
    db: Session = Depends(get_db)
):
    """
    Configura uma nova integração para uma clínica.
    
    Tipos suportados:
    - **google_calendar**: Sincronização com Google Agenda
    - **whatsapp**: Integração com WhatsApp Business
    - **telegram**: Bot do Telegram para notificações
    - **outlook**: Microsoft Outlook Calendar (futuro)
    
    Regras:
    - Cada clínica pode ter apenas UMA integração por tipo
    - Credenciais são validadas conforme o tipo
    """
    logger.info(f"Requisição POST /integracoes - Clínica: {integracao_data.clinica_id}")
    return integracao_service.criar_integracao(db, integracao_data)

# =====================================================
# GET - Listar integrações
# =====================================================

@router.get(
    "/",
    response_model=IntegracaoListResponse,
    summary="Listar integrações"
)
async def listar_integracoes(
    clinica_id: Optional[str] = Query(None, description="Filtrar por clínica"),
    tipo_servico: Optional[str] = Query(None, description="Filtrar por tipo (google_calendar, whatsapp, telegram)"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=500, description="Limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as integrações com filtros opcionais.
    
    - Se `clinica_id` for informado, retorna apenas daquela clínica
    - Se `tipo_servico` for informado, filtra por tipo
    - Se `ativo` for informado, filtra por status
    """
    logger.debug("Requisição GET /integracoes")
    
    integracoes, total = integracao_service.listar_integracoes(
        db=db,
        clinica_id=clinica_id,
        tipo_servico=tipo_servico,
        ativo=ativo,
        skip=skip,
        limit=limit
    )
    
    return {
        "mensagem": f"Encontradas {total} integrações",
        "total": total,
        "integracoes": integracoes
    }

# =====================================================
# GET - Buscar integração por ID
# =====================================================

@router.get(
    "/{integracao_id}",
    response_model=IntegracaoResponse,
    summary="Buscar integração por ID"
)
async def obter_integracao(
    integracao_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna os detalhes de uma integração específica.
    """
    logger.debug(f"Requisição GET /integracoes/{integracao_id}")
    return integracao_service.get_integracao_by_id(db, integracao_id)

# =====================================================
# GET - Buscar integração por clínica e tipo
# =====================================================

@router.get(
    "/clinica/{clinica_id}/tipo/{tipo_servico}",
    response_model=IntegracaoResponse,
    summary="Buscar integração por clínica e tipo"
)
async def obter_integracao_por_clinica_tipo(
    clinica_id: str,
    tipo_servico: str,
    db: Session = Depends(get_db)
):
    """
    Retorna a integração de uma clínica para um tipo específico.
    Útil para serviços que precisam da integração ativa.
    """
    logger.debug(f"Requisição GET /integracoes/clinica/{clinica_id}/tipo/{tipo_servico}")
    return integracao_service.get_integracao_by_clinica_and_tipo(db, clinica_id, tipo_servico)

# =====================================================
# PUT - Atualizar integração
# =====================================================

@router.put(
    "/{integracao_id}",
    response_model=IntegracaoResponse,
    summary="Atualizar integração"
)
async def atualizar_integracao(
    integracao_id: str,
    integracao_data: IntegracaoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados de uma integração existente.
    
    - Pode atualizar tipo_servico, credenciais e/ou status
    - Se mudar o tipo, valida unicidade
    - Credenciais são validadas conforme o tipo
    """
    logger.info(f"Requisição PUT /integracoes/{integracao_id}")
    return integracao_service.atualizar_integracao(db, integracao_id, integracao_data)

# =====================================================
# PATCH - Ativar/desativar integração
# =====================================================

@router.patch(
    "/{integracao_id}/ativar",
    response_model=IntegracaoResponse,
    summary="Ativar/desativar integração"
)
async def ativar_integracao(
    integracao_id: str,
    ativo: bool = Query(..., description="True para ativar, False para desativar"),
    db: Session = Depends(get_db)
):
    """
    Ativa ou desativa uma integração.
    
    - Útil para desabilitar temporariamente sem perder configurações
    """
    logger.info(f"Requisição PATCH /integracoes/{integracao_id}/ativar?ativo={ativo}")
    return integracao_service.ativar_integracao(db, integracao_id, ativo)

# =====================================================
# DELETE - Remover integração
# =====================================================

@router.delete(
    "/{integracao_id}",
    status_code=status.HTTP_200_OK,
    summary="Remover integração"
)
async def deletar_integracao(
    integracao_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove permanentemente uma integração.
    
    Cuidado: Esta ação não pode ser desfeita.
    Para desabilitar temporariamente, use PATCH /ativar com ativo=false
    """
    logger.warning(f"Requisição DELETE /integracoes/{integracao_id}")
    return integracao_service.deletar_integracao(db, integracao_id)

# =====================================================
# POST - Testar integração
# =====================================================

@router.post(
    "/{integracao_id}/testar",
    response_model=IntegracaoTesteResponse,
    summary="Testar conexão da integração"
)
async def testar_integracao(
    integracao_id: str,
    teste_data: Optional[IntegracaoTesteRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Testa se a integração está funcionando corretamente.
    
    - Usa as credenciais salvas por padrão
    - Pode fornecer `credenciais_teste` para testar novas configurações
    """
    logger.info(f"Requisição POST /integracoes/{integracao_id}/testar")
    
    credenciais_teste = teste_data.credenciais_teste if teste_data else None
    
    return integracao_service.testar_integracao(
        db, 
        integracao_id, 
        credenciais_teste
    )

# =====================================================
# GET - Estatísticas de integrações (opcional)
# =====================================================

@router.get(
    "/estatisticas",
    summary="Estatísticas de integrações"
)
async def estatisticas_integracoes(
    clinica_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas sobre as integrações.
    """
    logger.debug("Requisição GET /integracoes/estatisticas")
    
    query = db.query(integracao_service.Integracao)
    if clinica_id:
        query = query.filter(integracao_service.Integracao.clinica_id == clinica_id)
    
    total = query.count()
    ativas = query.filter(integracao_service.Integracao.ativo == True).count()
    
    # Contagem por tipo
    tipos = {}
    for tipo in ['google_calendar', 'whatsapp', 'telegram', 'outlook']:
        count = query.filter(integracao_service.Integracao.tipo_servico == tipo).count()
        if count > 0:
            tipos[tipo] = count
    
    return {
        "total_integracoes": total,
        "ativas": ativas,
        "inativas": total - ativas,
        "por_tipo": tipos
    }