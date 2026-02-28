from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from yumi.schemas.schemas_clinica_func import (
    ClinicaFuncionamentoCreate,
    ClinicaFuncionamentoUpdate,
)

from yumi.models.clinica_funcionamento import ClinicaFuncionamento
from yumi.services.clinica_service import get_clinica_by_id  # Reaproveita
from yumi.utils.uuid_generator import gerar_uuid

# =====================================================
# VALIDAÇÕES AUXILIARES (PRIVADAS)
# =====================================================

def _validar_dia_semana_unico(db: Session, clinica_id: str, dia_semana: int, horario_id: str = None):
    """
    Verifica se já existe horário para este dia na clínica.
    Se horario_id for fornecido, ignora na verificação (para updates).
    """
    query = db.query(ClinicaFuncionamento).filter(
        ClinicaFuncionamento.clinica_id == clinica_id,
        ClinicaFuncionamento.dia_semana == dia_semana
    )
    
    if horario_id:
        query = query.filter(ClinicaFuncionamento.id != horario_id)
    
    existente = query.first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe horário cadastrado para o dia {dia_semana}"
        )

# =====================================================
# CRUD - FUNCIONAMENTO
# =====================================================

def criar_horario(
    db: Session, 
    clinica_id: str, 
    horario_data: ClinicaFuncionamentoCreate
):
    """
    Cria um novo horário de funcionamento para uma clínica.
    """
    # 1. Verifica se a clínica existe
    clinica = get_clinica_by_id(db, clinica_id)
    
    # 2. Verifica se já existe horário para este dia
    _validar_dia_semana_unico(db, clinica_id, horario_data.dia_semana)
    
    # 3. Cria o horário
    novo_horario = ClinicaFuncionamento(
        id=gerar_uuid(),
        clinica_id=clinica_id,
        dia_semana=horario_data.dia_semana,
        hora_abertura=horario_data.hora_abertura,
        hora_fechamento=horario_data.hora_fechamento
    )
    
    db.add(novo_horario)
    db.commit()
    db.refresh(novo_horario)
    
    return novo_horario

def listar_horarios(db: Session, clinica_id: str):
    """
    Lista todos os horários de funcionamento de uma clínica.
    """
    # Verifica se a clínica existe
    clinica = get_clinica_by_id(db, clinica_id)
    
    return db.query(ClinicaFuncionamento).filter(
        ClinicaFuncionamento.clinica_id == clinica_id
    ).order_by(ClinicaFuncionamento.dia_semana).all()

def get_horario_by_id(db: Session, horario_id: str):
    """
    Busca um horário específico por ID.
    """
    horario = db.query(ClinicaFuncionamento).filter(
        ClinicaFuncionamento.id == horario_id
    ).first()
    
    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Horário com ID {horario_id} não encontrado"
        )
    
    return horario

def get_horario_by_dia(db: Session, clinica_id: str, dia_semana: int):
    """
    Busca o horário de um dia específico.
    """
    horario = db.query(ClinicaFuncionamento).filter(
        ClinicaFuncionamento.clinica_id == clinica_id,
        ClinicaFuncionamento.dia_semana == dia_semana
    ).first()
    
    if not horario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Não há horário cadastrado para o dia {dia_semana}"
        )
    
    return horario

def atualizar_horario(
    db: Session,
    horario_id: str,
    horario_data: ClinicaFuncionamentoUpdate
):
    """
    Atualiza um horário existente.
    """
    # 1. Busca o horário
    horario = get_horario_by_id(db, horario_id)
    
    # 2. Se estiver mudando o dia, verifica unicidade
    if horario_data.dia_semana is not None and horario_data.dia_semana != horario.dia_semana:
        _validar_dia_semana_unico(
            db, 
            horario.clinica_id, 
            horario_data.dia_semana,
            horario_id  # Ignora o próprio na verificação
        )
    
    # 3. Atualiza apenas os campos enviados
    update_data = horario_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(horario, field, value)
    
    db.commit()
    db.refresh(horario)
    
    return horario

def deletar_horario(db: Session, horario_id: str):
    """
    Remove um horário (delete físico mesmo).
    """
    horario = get_horario_by_id(db, horario_id)
    
    db.delete(horario)
    db.commit()
    
    return {"mensagem": "Horário removido com sucesso"}

# =====================================================
# UTILIDADES
# =====================================================

def verificar_disponibilidade(
    db: Session,
    clinica_id: str,
    dia_semana: int,
    hora: str
) -> bool:
    """
    Verifica se um determinado horário está dentro do funcionamento da clínica.
    Útil para validar agendamentos.
    """
    try:
        horario = get_horario_by_dia(db, clinica_id, dia_semana)
        return horario.hora_abertura <= hora <= horario.hora_fechamento
    except HTTPException:
        # Se não tem horário cadastrado, clínica não funciona neste dia
        return False