from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_clinica_func import (
    ClinicaFuncionamentoCreate,
    ClinicaFuncionamentoListResponse,
    ClinicaFuncionamentoResponse,
    ClinicaFuncionamentoUpdate,
)
from yumi.services import clinica_func_service

router = APIRouter()

# =====================================================
# POST - Criar novo horário
# =====================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClinicaFuncionamentoResponse,
    summary="Adicionar horário de funcionamento"
)
async def criar_horario(
    clinica_id: str,
    horario_data: ClinicaFuncionamentoCreate,
    db: Session = Depends(get_db)
):
    """
    Adiciona um novo horário de funcionamento para a clínica.
    
    - **dia_semana**: 0=Dom, 1=Seg, 2=Ter, 3=Qua, 4=Qui, 5=Sex, 6=Sáb
    - **hora_abertura**: Formato HH:MM (ex: 08:00)
    - **hora_fechamento**: Formato HH:MM (ex: 18:00)
    
    Regras:
    - Não pode haver dois horários para o mesmo dia
    - Fechamento deve ser maior que abertura
    """
    logger.info(f"Requisição POST /funcionamento - Criando horário para clínica {clinica_id}, dia {horario_data.dia_semana}")
    try:
        return clinica_func_service.criar_horario(db, clinica_id, horario_data)
    except Exception:
        logger.error(f"Erro ao criar horário para clínica {clinica_id}", exc_info=True)
        raise

# =====================================================
# GET - Listar todos os horários
# =====================================================

@router.get(
    "/",
    response_model=ClinicaFuncionamentoListResponse,
    summary="Listar horários de funcionamento"
)
async def listar_horarios(
    clinica_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna todos os horários de funcionamento cadastrados para a clínica.
    Ordenados por dia da semana (0 a 6).
    """
    logger.debug(f"Requisição GET /funcionamento - Listando horários da clínica {clinica_id}")
    horarios = clinica_func_service.listar_horarios(db, clinica_id)
    
    return {
        "mensagem": f"Encontrados {len(horarios)} horários",
        "total": len(horarios),
        "horarios": horarios
    }

# =====================================================
# GET - Buscar horário por dia da semana
# =====================================================

@router.get(
    "/{dia_semana}",
    response_model=ClinicaFuncionamentoResponse,
    summary="Buscar horário por dia da semana"
)
async def obter_horario_por_dia(
    clinica_id: str,
    dia_semana: int = Path(..., ge=0, le=6, description="0=Dom a 6=Sáb"),
    db: Session = Depends(get_db)
):
    """
    Retorna o horário de funcionamento para um dia específico.
    """
    logger.debug(f"Requisição GET /funcionamento/{dia_semana} - Clínica {clinica_id}")
    return clinica_func_service.get_horario_by_dia(db, clinica_id, dia_semana)

# =====================================================
# PUT - Atualizar horário por ID
# =====================================================

@router.put(
    "/{horario_id}",
    response_model=ClinicaFuncionamentoResponse,
    summary="Atualizar horário por ID"
)
async def atualizar_horario(
    clinica_id: str,  # Mantido para consistência, mas não usado diretamente
    horario_id: str,
    horario_data: ClinicaFuncionamentoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um horário específico.
    
    Todos os campos são opcionais.
    Se mudar o dia_semana, verifica se já não existe horário para o novo dia.
    """
    logger.info(f"Requisição PUT /funcionamento/{horario_id} - Atualizando horário")
    try:
        return clinica_func_service.atualizar_horario(db, horario_id, horario_data)
    except Exception:
        logger.error(f"Erro ao atualizar horário {horario_id}", exc_info=True)
        raise

# =====================================================
# DELETE - Remover horário
# =====================================================

@router.delete(
    "/{horario_id}",
    status_code=status.HTTP_200_OK,
    summary="Remover horário"
)
async def deletar_horario(
    clinica_id: str,  # Mantido para consistência
    horario_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove um horário de funcionamento.
    """
    logger.info(f"Requisição DELETE /funcionamento/{horario_id} - Removendo horário")
    try:
        return clinica_func_service.deletar_horario(db, horario_id)
    except Exception:
        logger.error(f"Erro ao deletar horário {horario_id}", exc_info=True)
        raise

# =====================================================
# UTILIDADE - Verificar disponibilidade de horário
# =====================================================

@router.get(
    "/verificar/{dia_semana}/{hora}",
    summary="Verificar se horário está dentro do funcionamento"
)
async def verificar_disponibilidade(
    clinica_id: str,
    dia_semana: int = Path(..., ge=0, le=6),
    hora: str = Path(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"),
    db: Session = Depends(get_db)
):
    """
    Verifica se um determinado horário está dentro do funcionamento da clínica.
    
    Útil para validar agendamentos antes de criar.
    """
    logger.debug(f"Verificando disponibilidade - Clínica {clinica_id}, dia {dia_semana}, {hora}")
    disponivel = clinica_func_service.verificar_disponibilidade(
        db, clinica_id, dia_semana, hora
    )
    
    return {
        "clinica_id": clinica_id,
        "dia_semana": dia_semana,
        "hora": hora,
        "disponivel": disponivel,
        "mensagem": "Horário disponível" if disponivel else "Fora do horário de funcionamento"
    }