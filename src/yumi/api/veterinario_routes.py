from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_agendamento import AgendamentoResponse
from yumi.schemas.schemas_veterinarios import VeterinarioCreate, VeterinarioUpdate
from yumi.services import veterinario_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_veterinario(
    veterinario_data: VeterinarioCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo veterinário."""
    logger.info(f"Requisição POST /veterinarios - Criando veterinário: {veterinario_data.nome}")
    
    try:
        # Chama o serviço (1 linha!)
        novo_veterinario = veterinario_service.create_veterinario(db, veterinario_data)
        
        # Monta resposta
        return {
            "mensagem": "Veterinário criado com sucesso",
            "veterinario": {
                "id": novo_veterinario.id,
                "nome": novo_veterinario.nome,
                "email": novo_veterinario.email,
                "especialidade": novo_veterinario.especialidade,
                "ativo": novo_veterinario.ativo,
                "created_at": novo_veterinario.created_at.isoformat() if novo_veterinario.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao criar veterinário {veterinario_data.nome}", exc_info=True)
        raise


@router.get("/{veterinario_id}", status_code=status.HTTP_200_OK)
async def obter_veterinario(
    veterinario_id: str,  # ← Parâmetro vindo da URL
    db: Session = Depends(get_db)
):
    """Obtém um veterinário específico por ID."""
    logger.info(f"Requisição GET /veterinarios/{veterinario_id} - Obtendo veterinário")
    
    try:
        veterinario = veterinario_service.get_veterinario_by_id(db, veterinario_id)
        return {
            "mensagem": "Veterinário encontrado",
            "veterinario": {
                "id": veterinario.id,
                "nome": veterinario.nome,
                "email": veterinario.email,
                "especialidade": veterinario.especialidade,
                "ativo": veterinario.ativo,
                "created_at": veterinario.created_at.isoformat() if veterinario.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao obter veterinário ID: {veterinario_id}", exc_info=True)
        raise


@router.get("/clinica/{clinica_id}", status_code=status.HTTP_200_OK)
async def listar_veterinarios_por_clinica(
    clinica_id: str,  # ← Parâmetro vindo da URL
    db: Session = Depends(get_db)
):
    """Lista todos os veterinários de uma clínica específica."""
    logger.info(f"Requisição GET /veterinarios/clinica/{clinica_id} - Listando veterinários por clínica")
    
    try:
        veterinarios = veterinario_service.get_veterinarios_by_clinica(db, clinica_id)
        return {
            "mensagem": f"Encontrados {len(veterinarios)} veterinário(s) para a clínica",
            "veterinarios": [
                {
                    "id": u.id,
                    "nome": u.nome,
                    "email": u.email,
                    "especialidade": u.especialidade,
                    "ativo": u.ativo,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                } for u in veterinarios
            ]
        }
    except Exception:
        logger.error(f"Erro ao listar veterinários para clínica ID: {clinica_id}", exc_info=True)
        raise


@router.put("/{veterinario_id}", status_code=status.HTTP_200_OK)
async def atualizar_veterinario(
    veterinario_id: str,
    veterinario_data: VeterinarioUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um veterinário existente."""
    logger.info(f"Requisição PUT /veterinarios/{veterinario_id} - Atualizando veterinário")
    
    try:
        veterinario_atualizado = veterinario_service.atualizar_veterinario(db, veterinario_id, veterinario_data)
        return {
            "mensagem": "Veterinário atualizado com sucesso",
            "veterinario": {
                "id": veterinario_atualizado.id,
                "nome": veterinario_atualizado.nome,
                "email": veterinario_atualizado.email,
                "especialidade": veterinario_atualizado.especialidade,
                "ativo": veterinario_atualizado.ativo,
                "created_at": veterinario_atualizado.created_at.isoformat() if veterinario_atualizado.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao atualizar veterinário ID: {veterinario_id}", exc_info=True)
        raise


@router.delete("/{veterinario_id}", status_code=status.HTTP_200_OK)
async def excluir_veterinario(
    veterinario_id: str,
    db: Session = Depends(get_db)
):
    """Exclui (desativa) um veterinário."""
    logger.info(f"Requisição DELETE /veterinarios/{veterinario_id} - Excluindo veterinário")
    
    try:
        veterinario_excluido = veterinario_service.delete_veterinario(db, veterinario_id)
        return {
            "mensagem": "Veterinário excluído (desativado) com sucesso",
            "veterinario": {
                "id": veterinario_excluido.id,
                "nome": veterinario_excluido.nome,
                "created_at": veterinario_excluido.created_at.isoformat() if veterinario_excluido.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao excluir veterinário ID: {veterinario_id}", exc_info=True)
        raise


@router.get("/{veterinario_id}/agendamentos", response_model=List[AgendamentoResponse])
async def listar_agendamentos_do_veterinario(
    veterinario_id: str,
    apenas_ativos: bool = Query(True, description="Excluir cancelados?"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir de"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até"),
    db: Session = Depends(get_db)
):
    """Retorna todos os agendamentos de um veterinário específico."""

    agendamentos = veterinario_service.get_agendamentos_por_veterinario(
        db,
        veterinario_id,
        apenas_ativos=apenas_ativos,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    return agendamentos
