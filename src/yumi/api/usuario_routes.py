from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_usuario import UsuarioCreate, UsuarioUpdate
from yumi.services import usuario_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo usuário."""
    logger.info(f"Requisição POST /usuarios - Criando usuário: {usuario_data.nome}")
    
    try:
        # Chama o serviço (1 linha!)
        novo_usuario = usuario_service.create_usuario(db, usuario_data)
        
        # Monta resposta
        return {
            "mensagem": "Usuário criado com sucesso",
            "usuario": {
                "id": novo_usuario.id,
                "nome": novo_usuario.nome,
                "email": novo_usuario.email,
                "ativo": novo_usuario.ativo,
                "created_at": novo_usuario.created_at.isoformat() if novo_usuario.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao criar usuário {usuario_data.nome}", exc_info=True)
        raise


@router.get("/{usuario_id}", status_code=status.HTTP_200_OK)
async def obter_usuario(
    usuario_id: str,  # ← Parâmetro vindo da URL
    db: Session = Depends(get_db)
):
    """Obtém um usuário específico por ID."""
    logger.info(f"Requisição GET /usuarios/{usuario_id} - Obtendo usuário")
    
    try:
        usuario = usuario_service.get_usuario_by_id(db, usuario_id)
        return {
            "mensagem": "Usuário encontrado",
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "cargo": usuario.role,
                "created_at": usuario.created_at.isoformat() if usuario.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao obter usuário ID: {usuario_id}", exc_info=True)
        raise


@router.get("/clinica/{clinica_id}", status_code=status.HTTP_200_OK)
async def listar_usuarios_por_clinica(
    clinica_id: str,  # ← Parâmetro vindo da URL
    db: Session = Depends(get_db)
):
    """Lista todos os usuários de uma clínica específica."""
    logger.info(f"Requisição GET /usuarios/clinica/{clinica_id} - Listando usuários por clínica")
    
    try:
        usuarios = usuario_service.get_usuarios_by_clinica(db, clinica_id)
        return {
            "mensagem": f"Encontrados {len(usuarios)} usuário(s) para a clínica",
            "usuarios": [
                {
                    "id": u.id,
                    "nome": u.nome,
                    "email": u.email,
                    "cargo": u.role,
                    "ativo": u.ativo,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                } for u in usuarios
            ]
        }
    except Exception:
        logger.error(f"Erro ao listar usuários para clínica ID: {clinica_id}", exc_info=True)
        raise


@router.put("/{usuario_id}", status_code=status.HTTP_200_OK)
async def atualizar_usuario(
    usuario_id: str,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um usuário existente."""
    logger.info(f"Requisição PUT /usuarios/{usuario_id} - Atualizando usuário")
    
    try:
        usuario_atualizado = usuario_service.atualizar_usuario(db, usuario_id, usuario_data)
        return {
            "mensagem": "Usuário atualizado com sucesso",
            "usuario": {
                "id": usuario_atualizado.id,
                "nome": usuario_atualizado.nome,
                "email": usuario_atualizado.email,
                "cargo": usuario_atualizado.role,
                "ativo": usuario_atualizado.ativo,
                "created_at": usuario_atualizado.created_at.isoformat() if usuario_atualizado.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao atualizar usuário ID: {usuario_id}", exc_info=True)
        raise


@router.delete("/{usuario_id}", status_code=status.HTTP_200_OK)
async def excluir_usuario(
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """Exclui (desativa) um usuário."""
    logger.info(f"Requisição DELETE /usuarios/{usuario_id} - Excluindo usuário")
    
    try:
        usuario_excluido = usuario_service.excluir_usuario(db, usuario_id)
        return {
            "mensagem": "Usuário excluído (desativado) com sucesso",
            "usuario": {
                "id": usuario_excluido.id,
                "nome": usuario_excluido.nome,
                "created_at": usuario_excluido.created_at.isoformat() if usuario_excluido.created_at else None
            }
        }
    except Exception:
        logger.error(f"Erro ao excluir usuário ID: {usuario_id}", exc_info=True)
        raise