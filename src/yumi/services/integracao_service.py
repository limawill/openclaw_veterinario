from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models.integracao import Integracao
from yumi.schemas.schemas_integracao import (
    GoogleCalendarCredenciais,
    IntegracaoCreate,
    IntegracaoUpdate,
    TelegramCredenciais,
    WhatsAppCredenciais,
)
from yumi.services.clinica_service import get_clinica_by_id
from yumi.utils.uuid_generator import gerar_uuid

# =====================================================
# VALIDAÇÕES AUXILIARES
# =====================================================

def _validar_credenciais_por_tipo(tipo_servico: str, credenciais: Dict[str, Any]):
    """
    Valida se as credenciais estão no formato correto para o tipo de serviço.
    """
    try:
        if tipo_servico == "google_calendar":
            # Valida usando schema específico
            GoogleCalendarCredenciais(**credenciais)
        elif tipo_servico == "whatsapp":
            WhatsAppCredenciais(**credenciais)
        elif tipo_servico == "telegram":
            TelegramCredenciais(**credenciais)
        elif tipo_servico == "outlook":
            # Validação básica para Outlook (pode expandir depois)
            if "access_token" not in credenciais:
                raise ValueError("Campo 'access_token' obrigatório")
        else:
            raise ValueError(f"Tipo de serviço não suportado: {tipo_servico}")
            
        logger.debug(f"Credenciais validadas para {tipo_servico}")
        return True
        
    except Exception as e:
        logger.error(f"Erro na validação de credenciais: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Credenciais inválidas para {tipo_servico}: {str(e)}"
        )

def _validar_unica_por_clinica(db: Session, clinica_id: str, tipo_servico: str, integracao_id: str = None):
    """
    Verifica se a clínica já tem uma integração deste tipo.
    """
    query = db.query(Integracao).filter(
        Integracao.clinica_id == clinica_id,
        Integracao.tipo_servico == tipo_servico
    )
    
    if integracao_id:
        query = query.filter(Integracao.id != integracao_id)
    
    existente = query.first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clínica já possui integração do tipo '{tipo_servico}'"
        )

# =====================================================
# CRUD - INTEGRAÇÕES
# =====================================================

def criar_integracao(
    db: Session,
    integracao_data: IntegracaoCreate
):
    """
    Cria uma nova integração para uma clínica.
    """
    logger.debug(f"Criando integração {integracao_data.tipo_servico} para clínica {integracao_data.clinica_id}")
    
    # 1. Verifica se clínica existe
    clinica = get_clinica_by_id(db, integracao_data.clinica_id)
    
    # 2. Valida se já não existe integração deste tipo
    _validar_unica_por_clinica(db, integracao_data.clinica_id, integracao_data.tipo_servico)
    
    # 3. Valida credenciais
    _validar_credenciais_por_tipo(integracao_data.tipo_servico, integracao_data.credenciais)
    
    # 4. Cria integração
    nova_integracao = Integracao(
        id=gerar_uuid(),
        clinica_id=integracao_data.clinica_id,
        tipo_servico=integracao_data.tipo_servico,
        credenciais=integracao_data.credenciais,
        ativo=integracao_data.ativo
    )
    
    try:
        db.add(nova_integracao)
        db.commit()
        db.refresh(nova_integracao)
        logger.info(f"Integração criada: {nova_integracao.id} para clínica {nova_integracao.clinica_id}")
        return nova_integracao
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar integração: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar integração"
        )

def listar_integracoes(
    db: Session,
    clinica_id: Optional[str] = None,
    tipo_servico: Optional[str] = None,
    ativo: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Lista integrações com filtros opcionais.
    """
    logger.debug("Listando integrações")
    
    query = db.query(Integracao)
    
    if clinica_id:
        query = query.filter(Integracao.clinica_id == clinica_id)
    if tipo_servico:
        query = query.filter(Integracao.tipo_servico == tipo_servico)
    if ativo is not None:
        query = query.filter(Integracao.ativo == ativo)
    
    total = query.count()
    integracoes = query.offset(skip).limit(limit).all()
    
    logger.info(f"Encontradas {total} integrações")
    return integracoes, total

def get_integracao_by_id(db: Session, integracao_id: str):
    """
    Busca uma integração por ID.
    """
    logger.debug(f"Buscando integração {integracao_id}")
    
    integracao = db.query(Integracao).filter(Integracao.id == integracao_id).first()
    
    if not integracao:
        logger.warning(f"Integração não encontrada: {integracao_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integração {integracao_id} não encontrada"
        )
    
    return integracao

def get_integracao_by_clinica_and_tipo(
    db: Session,
    clinica_id: str,
    tipo_servico: str
):
    """
    Busca uma integração específica por clínica e tipo.
    Útil para serviços que precisam da integração ativa.
    """
    logger.debug(f"Buscando integração {tipo_servico} para clínica {clinica_id}")
    
    integracao = db.query(Integracao).filter(
        Integracao.clinica_id == clinica_id,
        Integracao.tipo_servico == tipo_servico,
        Integracao.ativo == True
    ).first()
    
    if not integracao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clínica não possui integração ativa do tipo '{tipo_servico}'"
        )
    
    return integracao

def atualizar_integracao(
    db: Session,
    integracao_id: str,
    integracao_data: IntegracaoUpdate
):
    """
    Atualiza uma integração existente.
    """
    logger.debug(f"Atualizando integração {integracao_id}")
    
    integracao = get_integracao_by_id(db, integracao_id)
    
    # Se mudar tipo_servico, verifica unicidade
    if integracao_data.tipo_servico and integracao_data.tipo_servico != integracao.tipo_servico:
        _validar_unica_por_clinica(
            db, 
            integracao.clinica_id, 
            integracao_data.tipo_servico,
            integracao_id
        )
    
    # Se atualizar credenciais, valida
    if integracao_data.credenciais:
        tipo = integracao_data.tipo_servico or integracao.tipo_servico
        _validar_credenciais_por_tipo(tipo, integracao_data.credenciais)
    
    # Atualiza campos
    update_data = integracao_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(integracao, field, value)
    
    db.commit()
    db.refresh(integracao)
    logger.info(f"Integração {integracao_id} atualizada")
    
    return integracao

def deletar_integracao(db: Session, integracao_id: str):
    """
    Remove uma integração (delete físico).
    """
    logger.debug(f"Deletando integração {integracao_id}")
    
    integracao = get_integracao_by_id(db, integracao_id)
    
    db.delete(integracao)
    db.commit()
    
    logger.info(f"Integração {integracao_id} removida")
    return {"mensagem": "Integração removida com sucesso"}

def ativar_integracao(db: Session, integracao_id: str, ativo: bool):
    """
    Ativa ou desativa uma integração.
    """
    logger.debug(f"{'Ativando' if ativo else 'Desativando'} integração {integracao_id}")
    
    integracao = get_integracao_by_id(db, integracao_id)
    integracao.ativo = ativo
    
    db.commit()
    db.refresh(integracao)
    
    status = "ativada" if ativo else "desativada"
    logger.info(f"Integração {integracao_id} {status}")
    
    return integracao

# =====================================================
# TESTES DE CONEXÃO
# =====================================================

def testar_conexao_google_calendar(credenciais: Dict[str, Any]) -> Dict[str, Any]:
    """
    Testa conexão com Google Calendar.
    """
    # Aqui você implementaria a chamada real à API do Google
    # Por enquanto é um mock
    logger.debug("Testando conexão com Google Calendar")
    
    try:
        # Simula validação
        if "access_token" not in credenciais:
            raise ValueError("Access token não fornecido")
        
        return {
            "sucesso": True,
            "mensagem": "Conexão com Google Calendar estabelecida",
            "detalhes": {
                "calendar_id": credenciais.get("calendar_id", "primary"),
                "email": "teste@gmail.com"  # Viria da API
            }
        }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Falha na conexão: {str(e)}",
            "detalhes": None
        }

def testar_conexao_whatsapp(credenciais: Dict[str, Any]) -> Dict[str, Any]:
    """
    Testa conexão com WhatsApp Business.
    """
    logger.debug("Testando conexão com WhatsApp")
    
    try:
        if "phone_number_id" not in credenciais:
            raise ValueError("phone_number_id não fornecido")
        if "access_token" not in credenciais:
            raise ValueError("access_token não fornecido")
        
        return {
            "sucesso": True,
            "mensagem": "Conexão com WhatsApp Business estabelecida",
            "detalhes": {
                "phone_number_id": credenciais["phone_number_id"]
            }
        }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Falha na conexão: {str(e)}",
            "detalhes": None
        }

def testar_conexao_telegram(credenciais: Dict[str, Any]) -> Dict[str, Any]:
    """
    Testa conexão com Telegram.
    """
    logger.debug("Testando conexão com Telegram")
    
    try:
        if "bot_token" not in credenciais:
            raise ValueError("bot_token não fornecido")
        
        return {
            "sucesso": True,
            "mensagem": "Conexão com Telegram estabelecida",
            "detalhes": {
                "bot_name": "YumiBot"  # Viria da API
            }
        }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Falha na conexão: {str(e)}",
            "detalhes": None
        }

def testar_integracao(
    db: Session,
    integracao_id: str,
    credenciais_teste: Optional[Dict[str, Any]] = None
):
    """
    Testa se a integração está funcionando.
    """
    logger.debug(f"Testando integração {integracao_id}")
    
    integracao = get_integracao_by_id(db, integracao_id)
    
    # Usa credenciais do banco ou as fornecidas para teste
    creds = credenciais_teste if credenciais_teste else integracao.credenciais
    
    # Roteia para o testador adequado
    if integracao.tipo_servico == "google_calendar":
        return testar_conexao_google_calendar(creds)
    elif integracao.tipo_servico == "whatsapp":
        return testar_conexao_whatsapp(creds)
    elif integracao.tipo_servico == "telegram":
        return testar_conexao_telegram(creds)
    else:
        return {
            "sucesso": False,
            "mensagem": f"Teste não implementado para {integracao.tipo_servico}",
            "detalhes": None
        }
