from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models.usuario import Usuario
from yumi.utils.tools import Tools
from yumi.utils.uuid_generator import gerar_uuid


def create_usuario(db: Session, usuario_data):
    """
    Regra de negócio para criar um usuário.
    Retorna o usuário criado ou levanta exceção.
    """
    logger.debug(f"Iniciando criação de usuário: {usuario_data.email}")
    
    # 1. Verifica duplicidade
    usuario_existente = db.query(Usuario).filter(
        Usuario.email == usuario_data.email
    ).first()
    
    if usuario_existente:
        logger.warning(
            f"Tentativa de criar usuário duplicado: {usuario_data.email} "
            f"(ID: {usuario_existente.id})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este email"
        )
    
    # 2. Cria instância
    novo_usuario = Usuario(
        id=gerar_uuid(),
        clinica_id=usuario_data.clinica_id,
        email=usuario_data.email,
        nome=usuario_data.nome,
        role=usuario_data.role,
        ativo=usuario_data.ativo
    )
    
    # 3. Persiste
    try:
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        logger.info(f"Usuário criado com sucesso: {novo_usuario.email} (ID: {novo_usuario.id})")
        return novo_usuario
    except Exception:
        db.rollback()
        logger.error(f"Erro ao criar usuário {usuario_data.email}", exc_info=True)
        raise


def get_usuario_by_id(db: Session, usuario_id: str):
    """
    Busca um usuário específico por ID.
    Retorna o usuário ou levanta 404 se não existir.
    """
    logger.debug(f"Buscando usuário com ID: {usuario_id}")
    
    # Remove espaços em branco que podem vir da URL
    usuario_id = Tools.remove_espaco_string(usuario_id)
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        logger.warning(f"Usuário não encontrado - ID solicitado: {usuario_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID '{usuario_id}' não encontrado"
        )
    
    logger.debug(f"Usuário encontrado: {usuario.nome} (ID: {usuario.id})")
    return usuario


def get_usuarios_by_clinica(db: Session, clinica_id: str):
    """
    Busca todos os usuários vinculados a uma clínica.
    Retorna lista de usuários ou vazia se não houver.
    """
    logger.debug(f"Buscando usuários para clínica ID: {clinica_id}")
    # Remove espaços em branco que podem vir da URL
    clinica_id = Tools.remove_espaco_string(clinica_id)
    usuarios = db.query(Usuario).filter(Usuario.clinica_id == clinica_id).all()
    
    logger.info(f"{len(usuarios)} usuário(s) encontrados para clínica ID: {clinica_id}")
    return usuarios


def atualizar_usuario(db: Session, usuario_id: str, usuario_data):
    """
    Regra de negócio para atualizar um usuário.
    Retorna o usuário atualizado ou levanta exceção.
    """
    logger.debug(f"Iniciando atualização de usuário ID: {usuario_id}")
    
    usuario = get_usuario_by_id(db, usuario_id)
    
    # Atualiza campos se foram fornecidos
    if usuario_data.nome is not None:
        usuario.nome = usuario_data.nome
    if usuario_data.email is not None:
        # Verifica duplicidade de email
        email_existente = db.query(Usuario).filter(
            Usuario.email == usuario_data.email,
            Usuario.id != usuario_id  # Ignora o próprio usuário
        ).first()
        if email_existente:
            logger.warning(
                f"Tentativa de atualizar usuário com email duplicado: {usuario_data.email} "
                f"(ID existente: {email_existente.id})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro usuário com este email"
            )
        usuario.email = usuario_data.email
    if usuario_data.role is not None:
        usuario.role = usuario_data.role
    if usuario_data.ativo is not None:
        usuario.ativo = usuario_data.ativo
    
    # Persiste alterações
    try:
        db.commit()
        db.refresh(usuario)
        logger.info(f"Usuário atualizado com sucesso: {usuario.nome} (ID: {usuario.id})")
        return usuario
    except Exception:
        db.rollback()
        logger.error(f"Erro ao atualizar usuário ID: {usuario_id}", exc_info=True)
        raise


def delete_usuario(db: Session, usuario_id: str):
    """
    Regra de negócio para deletar um usuário.
    Retorna mensagem de sucesso ou levanta exceção.
    """
    logger.debug(f"Iniciando exclusão de usuário ID: {usuario_id}")
    usuario = get_usuario_by_id(db, usuario_id)
    usuario.ativo = False
    db.commit()
    db.refresh(usuario)
    return usuario
