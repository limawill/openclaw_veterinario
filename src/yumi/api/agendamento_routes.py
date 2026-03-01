# src/yumi/api/agendamento_routes.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_agendamento import (
    AgendamentoCreate,
    AgendamentoListResponse,
    AgendamentoResponse,
    AgendamentoUpdate,
)
from yumi.services import agendamento_service

router = APIRouter()

# =====================================================
# POST - Criar agendamento
# =====================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=AgendamentoResponse,
    summary="Criar novo agendamento"
)
async def criar_agendamento(
    agendamento_data: AgendamentoCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo agendamento.
    
    Regras:
    - Horário deve estar dentro do funcionamento da clínica
    - Veterinário não pode ter outro agendamento no mesmo horário
    - Status inicial: 'agendado' (padrão)
    """
    logger.info(f"Requisição POST /agendamentos - Cliente: {agendamento_data.nome_cliente}")
    return agendamento_service.criar_agendamento(db, agendamento_data)

# =====================================================
# GET - Listar agendamentos com filtros
# =====================================================

@router.get(
    "/",
    response_model=AgendamentoListResponse,
    summary="Listar agendamentos"
)
async def listar_agendamentos(
    clinica_id: Optional[str] = Query(None, description="Filtrar por clínica"),
    veterinario_id: Optional[str] = Query(None, description="Filtrar por veterinário"),
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="agendado, confirmado, cancelado, concluido"),
    origem: Optional[str] = Query(None, description="chatbot, manual, whatsapp, telegram"),
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=500, description="Limite de registros"),
    db: Session = Depends(get_db)
):
    """
    Lista agendamentos com diversos filtros opcionais.
    
    - Se nenhum filtro for informado, retorna os últimos 100 agendamentos
    - Ordenados por data/hora (mais recentes primeiro)
    """
    logger.debug("Requisição GET /agendamentos com filtros")
    
    agendamentos, total = agendamento_service.listar_agendamentos(
        db=db,
        clinica_id=clinica_id,
        veterinario_id=veterinario_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status=status,
        origem=origem,
        skip=skip,
        limit=limit
    )
    
    return {
        "mensagem": f"Encontrados {total} agendamentos",
        "total": total,
        "agendamentos": agendamentos
    }

# =====================================================
# GET - Buscar agendamento por ID
# =====================================================

@router.get(
    "/{agendamento_id}",
    response_model=AgendamentoResponse,
    summary="Buscar agendamento por ID"
)
async def obter_agendamento(
    agendamento_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna os detalhes de um agendamento específico.
    """
    logger.debug(f"Requisição GET /agendamentos/{agendamento_id}")
    return agendamento_service.get_agendamento_by_id(db, agendamento_id)

# =====================================================
# PUT - Atualizar agendamento
# =====================================================

@router.put(
    "/{agendamento_id}",
    response_model=AgendamentoResponse,
    summary="Atualizar agendamento"
)
async def atualizar_agendamento(
    agendamento_id: str,
    agendamento_data: AgendamentoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um agendamento existente.
    
    - Se mudar data/hora, valida disponibilidade novamente
    - Campos não enviados permanecem inalterados
    """
    logger.info(f"Requisição PUT /agendamentos/{agendamento_id}")
    return agendamento_service.atualizar_agendamento(db, agendamento_id, agendamento_data)

# =====================================================
# PATCH - Cancelar agendamento (rota específica)
# =====================================================

@router.patch(
    "/{agendamento_id}/cancelar",
    response_model=AgendamentoResponse,
    summary="Cancelar agendamento"
)
async def cancelar_agendamento(
    agendamento_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancela um agendamento (status = 'cancelado').
    """
    logger.info(f"Requisição PATCH /agendamentos/{agendamento_id}/cancelar")
    return agendamento_service.cancelar_agendamento(db, agendamento_id)

# =====================================================
# DELETE - Remover agendamento (físico - apenas admin)
# =====================================================

@router.delete(
    "/{agendamento_id}",
    status_code=status.HTTP_200_OK,
    summary="Remover agendamento (admin)"
)
async def deletar_agendamento(
    agendamento_id: str,
    db: Session = Depends(get_db),
    admin_key: str = Query(..., description="Chave de admin para deletar físico")
):
    """
    Remove fisicamente um agendamento (apenas admin master).
    
    - Uso restrito (correção de dados)
    - Para uso normal, prefira PATCH /cancelar
    """
    # Validação simples de admin (depois melhorar com auth real)
    if admin_key != "admin-secret-123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para admin"
        )
    
    agendamento = agendamento_service.get_agendamento_by_id(db, agendamento_id)
    db.delete(agendamento)
    db.commit()
    
    logger.warning(f"Agendamento {agendamento_id} removido fisicamente por admin")
    return {"mensagem": "Agendamento removido permanentemente"}

# =====================================================
# GET - Verificar disponibilidade de horários
# =====================================================

@router.get(
    "/disponibilidade/verificar",
    summary="Verificar horários disponíveis"
)
async def verificar_disponibilidade(
    veterinario_id: str = Query(..., description="ID do veterinário"),
    data: date = Query(..., description="Data para consulta (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Retorna os horários ocupados para um veterinário em uma data específica.
    Útil para frontend/chatbot mostrar disponibilidade.
    """
    logger.debug(f"Verificando disponibilidade para vet {veterinario_id} em {data}")

    return agendamento_service.verificar_disponibilidade(
        db,
        veterinario_id,
        data
    )
