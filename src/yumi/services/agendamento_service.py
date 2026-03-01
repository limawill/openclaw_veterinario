from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models.agendamento import Agendamento
from yumi.schemas.schemas_agendamento import AgendamentoCreate, AgendamentoUpdate
from yumi.services.clinica_service import get_clinica_by_id
from yumi.services.veterinario_service import get_veterinario_by_id
from yumi.utils.uuid_generator import gerar_uuid

# =====================================================
# VALIDAÇÕES AUXILIARES
# =====================================================


def _mapear_dia_semana_clinica(data_ref: datetime) -> int:
    """
    Converte datetime.weekday() para o padrão da clínica.

    - Python: 0=Seg, ..., 6=Dom
    - Clínica: 0=Dom, 1=Seg, ..., 6=Sáb
    """
    return (data_ref.weekday() + 1) % 7

def _validar_disponibilidade(
    db: Session,
    veterinario_id: str,
    data_inicio: datetime,
    data_fim: datetime,
    agendamento_id: Optional[str] = None
):
    """
    Verifica se o horário está disponível para o veterinário.
    """
    # Constrói query base
    query = db.query(Agendamento).filter(
        Agendamento.veterinario_id == veterinario_id,
        Agendamento.status != "cancelado",  # Ignora cancelados
        and_(
            Agendamento.data_hora_inicio < data_fim,
            Agendamento.data_hora_fim > data_inicio
        )
    )
    
    # Se for atualização, ignora o próprio agendamento
    if agendamento_id:
        query = query.filter(Agendamento.id != agendamento_id)
    
    conflito = query.first()
    
    if conflito:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Horário já ocupado para este veterinário. "
                   f"Conflito com agendamento {conflito.id}"
        )

def _validar_horario_funcionamento(
    db: Session,
    clinica_id: str,
    data_inicio: datetime,
    data_fim: datetime
):
    """
    Verifica se o horário está dentro do funcionamento da clínica.
    """
    from yumi.services.clinica_func_service import get_horario_by_dia

    if data_fim <= data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data_hora_fim deve ser maior que data_hora_inicio"
        )

    if data_inicio.date() != data_fim.date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agendamento deve iniciar e terminar no mesmo dia"
        )

    dia_semana = _mapear_dia_semana_clinica(data_inicio)
    hora_inicio_str = data_inicio.strftime("%H:%M")
    hora_fim_str = data_fim.strftime("%H:%M")

    try:
        horario = get_horario_by_dia(db, clinica_id, dia_semana)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clínica não possui horário de funcionamento para este dia"
        )

    dentro_do_funcionamento = (
        horario.hora_abertura <= hora_inicio_str
        and hora_fim_str <= horario.hora_fechamento
    )

    if not dentro_do_funcionamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Horário fora do funcionamento da clínica "
                f"({horario.hora_abertura} às {horario.hora_fechamento})"
            )
        )

# =====================================================
# CRUD - AGENDAMENTOS
# =====================================================

def criar_agendamento(
    db: Session,
    agendamento_data: AgendamentoCreate
):
    """
    Cria um novo agendamento.
    """
    logger.debug(f"Criando agendamento para veterinário {agendamento_data.veterinario_id}")
    
    # 1. Verifica se clínica e veterinário existem
    clinica = get_clinica_by_id(db, agendamento_data.clinica_id)
    veterinario = get_veterinario_by_id(db, agendamento_data.veterinario_id)
    
    # 2. Valida horário de funcionamento
    _validar_horario_funcionamento(
        db,
        agendamento_data.clinica_id,
        agendamento_data.data_hora_inicio,
        agendamento_data.data_hora_fim
    )
    
    # 3. Valida disponibilidade
    _validar_disponibilidade(
        db,
        agendamento_data.veterinario_id,
        agendamento_data.data_hora_inicio,
        agendamento_data.data_hora_fim
    )
    
    # 4. Cria agendamento
    novo_agendamento = Agendamento(
        id=gerar_uuid(),
        clinica_id=agendamento_data.clinica_id,
        veterinario_id=agendamento_data.veterinario_id,
        nome_cliente=agendamento_data.nome_cliente,
        telefone_cliente=agendamento_data.telefone_cliente,
        nome_pet=agendamento_data.nome_pet,
        data_hora_inicio=agendamento_data.data_hora_inicio,
        data_hora_fim=agendamento_data.data_hora_fim,
        status=agendamento_data.status,
        origem=agendamento_data.origem,
        id_evento_externo=agendamento_data.id_evento_externo
    )
    
    try:
        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)
        logger.info(f"Agendamento criado: {novo_agendamento.id}")
        
        # Adicionando dados para um return melhor
        novo_agendamento_dict = novo_agendamento.__dict__.copy()
        novo_agendamento_dict["nome_veterinario"] = veterinario.nome if veterinario else None
        novo_agendamento_dict["nome_clinica"] = clinica.nome if clinica else None
        return novo_agendamento_dict
    
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar agendamento"
        )

def listar_agendamentos(
    db: Session,
    clinica_id: Optional[str] = None,
    veterinario_id: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    status: Optional[str] = None,
    origem: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Lista agendamentos com filtros.
    """
    logger.debug("Listando agendamentos com filtros")
    
    query = db.query(Agendamento)
    
    # Aplica filtros
    if clinica_id:
        query = query.filter(Agendamento.clinica_id == clinica_id)
    if veterinario_id:
        query = query.filter(Agendamento.veterinario_id == veterinario_id)
    if data_inicio:
        query = query.filter(Agendamento.data_hora_inicio >= data_inicio)
    if data_fim:
        query = query.filter(Agendamento.data_hora_fim <= data_fim)
    if status:
        query = query.filter(Agendamento.status == status)
    if origem:
        query = query.filter(Agendamento.origem == origem)
    
    # Ordena por data (mais recentes primeiro)
    query = query.order_by(Agendamento.data_hora_inicio.desc())
    
    total = query.count()
    agendamentos = query.offset(skip).limit(limit).all()
    
    logger.info(f"Encontrados {total} agendamentos")
    return agendamentos, total

def get_agendamento_by_id(db: Session, agendamento_id: str):
    """
    Busca um agendamento por ID.
    """
    logger.debug(f"Buscando agendamento {agendamento_id}")
    
    agendamento = db.query(Agendamento).filter(
        Agendamento.id == agendamento_id
    ).first()
    
    if not agendamento:
        logger.warning(f"Agendamento não encontrado: {agendamento_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {agendamento_id} não encontrado"
        )
    
    return agendamento

def atualizar_agendamento(
    db: Session,
    agendamento_id: str,
    agendamento_data: AgendamentoUpdate
):
    """
    Atualiza um agendamento existente.
    """
    logger.debug(f"Atualizando agendamento {agendamento_id}")
    
    agendamento = get_agendamento_by_id(db, agendamento_id)
    
    # Se mudar data/hora, valida disponibilidade novamente
    if agendamento_data.data_hora_inicio or agendamento_data.data_hora_fim:
        data_inicio = agendamento_data.data_hora_inicio or agendamento.data_hora_inicio
        data_fim = agendamento_data.data_hora_fim or agendamento.data_hora_fim
        
        _validar_disponibilidade(
            db,
            agendamento.veterinario_id,
            data_inicio,
            data_fim,
            agendamento_id
        )
    
    # Atualiza campos
    update_data = agendamento_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agendamento, field, value)
    
    db.commit()
    db.refresh(agendamento)
    logger.info(f"Agendamento {agendamento_id} atualizado")
    
    return agendamento

def cancelar_agendamento(db: Session, agendamento_id: str):
    """
    Cancela um agendamento (soft delete via status).
    """
    logger.debug(f"Cancelando agendamento {agendamento_id}")
    
    agendamento = get_agendamento_by_id(db, agendamento_id)
    agendamento.status = "cancelado"
    
    db.commit()
    db.refresh(agendamento)
    logger.info(f"Agendamento {agendamento_id} cancelado")
    
    return agendamento

def verificar_disponibilidade(
    db: Session,
    veterinario_id: str,
    data: date
):
    """
    Retorna horários disponíveis para um veterinário em uma data específica.
    """
    logger.debug(f"Verificando disponibilidade para veterinário {veterinario_id} em {data}")
    
    # Busca agendamentos do dia
    inicio_dia = datetime.combine(data, datetime.min.time())
    fim_dia = datetime.combine(data, datetime.max.time())
    
    agendamentos = db.query(Agendamento).filter(
        Agendamento.veterinario_id == veterinario_id,
        Agendamento.status != "cancelado",
        and_(
            Agendamento.data_hora_inicio >= inicio_dia,
            Agendamento.data_hora_fim <= fim_dia
        )
    ).order_by(Agendamento.data_hora_inicio).all()
    
    # Aqui você pode implementar lógica para retornar slots disponíveis
    # Baseado nos horários de funcionamento da clínica e agendamentos existentes
    
    return {
        "veterinario_id": veterinario_id,
        "data": data.isoformat(),
        "agendamentos_existentes": len(agendamentos),
        "horarios_ocupados": [
            {
                "inicio": a.data_hora_inicio.isoformat(),
                "fim": a.data_hora_fim.isoformat(),
                "status": a.status
            }
            for a in agendamentos
        ]
    }