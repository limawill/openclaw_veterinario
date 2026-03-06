from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.auth.security import (
    criar_refresh_token,
    criar_token_jwt,
    decodificar_token_jwt,
    verificar_senha,
)
from yumi.core.config import settings
from yumi.core.logger import logger
from yumi.models.refresh_token import RefreshToken
from yumi.models.usuario import Usuario
from yumi.utils.uuid_generator import gerar_uuid

# =====================================================
# FUNÇÕES AUXILIARES (INTERNAS)
# =====================================================

def _get_usuario_por_email(db: Session, email: str) -> Usuario:
    """
    Busca um usuário pelo email.
    
    Args:
        db: Sessão do banco
        email: Email do usuário
        
    Returns:
        Usuario encontrado
        
    Raises:
        HTTPException 404 se não encontrar
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario:
        logger.warning(f"Tentativa de login com email não cadastrado: {email}")
        # Mensagem genérica por segurança (não revelar se usuário existe)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return usuario

def _validar_usuario_ativo(usuario: Usuario) -> None:
    """
    Verifica se o usuário está ativo.
    
    Args:
        usuario: Usuário a verificar
        
    Raises:
        HTTPException 403 se estiver inativo
    """
    if not usuario.ativo:
        logger.warning(f"Tentativa de login com usuário inativo: {usuario.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador."
        )

def _validar_senha(senha: str, hash_armazenado: str) -> None:
    """
    Valida se a senha corresponde ao hash.
    
    Args:
        senha: Senha fornecida (texto puro)
        hash_armazenado: Hash salvo no banco
        
    Raises:
        HTTPException 401 se senha inválida
    """
    try:
        senha_valida = verificar_senha(senha, hash_armazenado)
    except ValueError:
        logger.error("Hash de senha inválido armazenado para usuário")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not senha_valida:
        logger.warning("Tentativa de login com senha inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _atualizar_ultimo_login(db: Session, usuario: Usuario) -> None:
    """
    Atualiza o timestamp do último login do usuário.
    
    Args:
        db: Sessão do banco
        usuario: Usuário que fez login
    """
    usuario.ultimo_login = datetime.now()
    db.commit()
    logger.info(f"Último login atualizado para usuário: {usuario.email}")

# =====================================================
# FUNÇÃO PRINCIPAL DE LOGIN
# =====================================================

def autenticar_usuario(db: Session, email: str, senha: str) -> dict:
    """
    Autentica um usuário e retorna tokens + dados do usuário.

    Fluxo completo:
    1. Busca usuário por email
    2. Verifica se está ativo
    3. Valida a senha
    4. Atualiza último login
    5. Gera tokens e retorna tudo em um único dict

    Args:
        db: Sessão do banco
        email: Email do usuário
        senha: Senha em texto puro

    Returns:
        Dict com access_token, refresh_token e dados básicos do usuário

    Raises:
        HTTPException 401/403 em caso de falha
    """
    logger.debug(f"Tentativa de login para email: {email}")
    
    # 1. Busca usuário
    usuario = _get_usuario_por_email(db, email)
    
    # 2. Verifica se está ativo
    _validar_usuario_ativo(usuario)
    
    # 3. Valida senha
    _validar_senha(senha, usuario.password_hash)
    
    # 4. Atualiza último login
    _atualizar_ultimo_login(db, usuario)
    
    # 5. Prepara payload do token
    payload = {
        "sub": usuario.id,              # subject = ID do usuário
        "clinica_id": usuario.clinica_id,
        "role": usuario.role,
        "email": usuario.email,          # opcional, útil para debug
        "nome": usuario.nome              # opcional, útil para frontend
    }
    
    # 6. Gera tokens
    access_token = criar_token_jwt(payload)
    refresh_token = criar_refresh_token({
        "sub": usuario.id,
        "clinica_id": usuario.clinica_id,
        "role": usuario.role
    })

    # 7. Persiste o refresh token no banco
    salvar_refresh_token(db, usuario_id=usuario.id, token=refresh_token)

    logger.info(f"Login bem-sucedido: {usuario.email} (role: {usuario.role})")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "role": usuario.role,
            "clinica_id": usuario.clinica_id,
        }
    }

# =====================================================
# FUNÇÕES DE REFRESH TOKEN
# =====================================================

def salvar_refresh_token(db: Session, usuario_id: str, token: str) -> None:
    """Persiste o refresh token no banco para controle de sessão."""
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    registro = RefreshToken(
        id=gerar_uuid(),
        usuario_id=usuario_id,
        token=token,
        expires_at=expires_at,
        revogado=False
    )
    db.add(registro)
    db.commit()
    logger.debug(f"Refresh token salvo para usuario_id={usuario_id}")


def renovar_tokens(db: Session, refresh_token: str) -> dict:
    """
    Valida o refresh token recebido e emite um novo par de tokens.

    Fluxo:
    1. Decodifica o JWT do refresh token
    2. Verifica se o type é "refresh"
    3. Busca o registro no banco e verifica se não foi revogado
    4. Revoga o token antigo (rotação: cada refresh token só pode ser usado uma vez)
    5. Gera e persiste um novo par access + refresh token

    Raises:
        HTTPException 401 se o token for inválido, expirado ou já revogado
    """
    from jose import JWTError


    # 1. Decodifica o JWT
    try:
        payload = decodificar_token_jwt(refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Garante que é um refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token fornecido não é um refresh token",
        )

    # 3. Busca no banco
    registro = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if not registro or registro.revogado:
        logger.warning(f"Tentativa de uso de refresh token inválido/revogado: usuario_id={payload.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou já utilizado",
        )

    # 4. Revoga o token antigo (rotação de tokens)
    registro.revogado = True
    db.commit()

    # 5. Gera novos tokens
    usuario = obter_usuario_por_id(db, payload["sub"])
    _validar_usuario_ativo(usuario)

    novo_payload = {
        "sub": usuario.id,
        "clinica_id": usuario.clinica_id,
        "role": usuario.role,
        "email": usuario.email,
        "nome": usuario.nome
    }
    novo_access = criar_token_jwt(novo_payload)
    novo_refresh = criar_refresh_token({
        "sub": usuario.id,
        "clinica_id": usuario.clinica_id,
        "role": usuario.role
    })
    salvar_refresh_token(db, usuario_id=usuario.id, token=novo_refresh)

    logger.info(f"Tokens renovados para usuario_id={usuario.id}")
    return {"access_token": novo_access, "refresh_token": novo_refresh}


def revogar_refresh_token(db: Session, refresh_token: str) -> None:
    """
    Revoga um refresh token específico (logout real).

    Marca o registro como revogado no banco — mesmo antes de vencer,
    o token não poderá mais ser utilizado.
    """
    registro = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if registro and not registro.revogado:
        registro.revogado = True
        db.commit()
        logger.info(f"Refresh token revogado para usuario_id={registro.usuario_id}")
    else:
        logger.warning("Tentativa de revogar refresh token não encontrado ou já revogado")


# =====================================================
# FUNÇÕES PARA OBTER DADOS DO USUÁRIO (USO INTERNO)
# =====================================================

def obter_usuario_por_id(db: Session, usuario_id: str) -> Usuario:
    """
    Busca um usuário pelo ID.
    Útil para as dependências de autenticação.
    
    Args:
        db: Sessão do banco
        usuario_id: ID do usuário
        
    Returns:
        Usuario encontrado
        
    Raises:
        HTTPException 404 se não encontrar
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        logger.error(f"Usuário ID {usuario_id} não encontrado (token válido?)")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return usuario