from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from yumi.auth.auth_service import (
    autenticar_usuario,
    renovar_tokens,
    revogar_refresh_token,
)
from yumi.auth.dependencies import get_current_user
from yumi.core.database import get_db
from yumi.core.limiter import limiter
from yumi.core.logger import logger

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

# =====================================================
# SCHEMAS DE RESPOSTA (internos)
# =====================================================


class UsuarioInfo(BaseModel):
    """Dados básicos do usuário retornados no login."""
    id: str
    nome: str
    email: str
    role: str
    clinica_id: str


class TokenResponse(BaseModel):
    """Schema para resposta do login com tokens e dados do usuário."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioInfo | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "usuario": {
                    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "nome": "João Silva",
                    "email": "joao@clinica.com",
                    "role": "admin",
                    "clinica_id": "a1b2c3-..."
                }
            }
        }


class LoginRequest(BaseModel):
    """Schema para documentação do login."""
    email: str
    senha: str


class RefreshRequest(BaseModel):
    """Schema para renovar tokens via refresh token."""
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """Schema para logout real via refresh token."""
    refresh_token: str


# =====================================================
# ENDPOINT DE LOGIN
# =====================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuário e obter token JWT",
    description="""
    Realiza o login do usuário e retorna um token JWT.
    
    O token deve ser incluído no header Authorization das requisições:
    
    Regras:
    - Email e senha são obrigatórios
    - Usuário deve estar ativo
    - Após 5 tentativas falhas, o IP é bloqueado temporariamente
    """,
    responses={
        200: {"description": "Login realizado com sucesso"},
        401: {"description": "Credenciais inválidas"},
        403: {"description": "Usuário inativo"},
        429: {"description": "Muitas tentativas - aguarde"}
    }
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login compatível com OAuth2.

    Recebe:
    - **username**: Email do usuário (campo username do form)
    - **password**: Senha do usuário

    Retorna:
    - **access_token**: Token JWT para usar nas requisições
    - **token_type**: Sempre "bearer"
    """
    logger.info(f"Tentativa de login para email: {form_data.username}")

    try:
        # Autentica o usuário — retorna dict com access_token e refresh_token
        tokens = autenticar_usuario(
            db=db,
            email=form_data.username,
            senha=form_data.password
        )

        logger.info(f"Login bem-sucedido: {form_data.username}")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            usuario=UsuarioInfo(**tokens["usuario"])
        )

    except HTTPException as e:
        # Relança exceções do service (já tratadas com status code correto)
        logger.warning(f"Falha no login para {form_data.username}: {e.detail}")
        raise

    except Exception as e:
        # Erro inesperado
        logger.error(f"Erro inesperado no login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no servidor. Tente novamente mais tarde."
        )


# =====================================================
# ENDPOINT DE LOGOUT (opcional - apenas para documentação)
# =====================================================


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar tokens via refresh token",
    description="""
    Recebe o refresh token e emite um novo par access + refresh token.

    O refresh token antigo é **revogado imediatamente** após o uso (rotação de tokens).
    Salve o novo refresh token retornado para a próxima renovação.
    """,
    responses={
        200: {"description": "Tokens renovados com sucesso"},
        401: {"description": "Refresh token inválido, expirado ou já utilizado"}
    }
)
async def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Renova o access token usando o refresh token.
    Implementa rotação: o refresh token usado é revogado e um novo é emitido.
    """
    logger.info("Solicitação de renovação de tokens recebida")
    tokens = renovar_tokens(db=db, refresh_token=body.refresh_token)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"]
    )


@router.post(
    "/logout",
    summary="Realizar logout",
    description="""
    Revoga o refresh token no banco de dados.

    Após o logout, o refresh token não poderá mais ser utilizado para renovar sessões,
    mesmo que ainda não tenha expirado.
    """,
    responses={
        200: {"description": "Logout realizado com sucesso"}
    }
)
async def logout(
    body: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Logout real: revoga o refresh token no banco.
    O access token expira naturalmente no seu tempo definido.
    """
    logger.info("Solicitação de logout recebida")
    revogar_refresh_token(db=db, refresh_token=body.refresh_token)
    return {"mensagem": "Logout realizado com sucesso"}


# =====================================================
# ENDPOINT PARA TESTAR TOKEN (OPCIONAL)
# =====================================================


@router.get(
    "/me",
    summary="Informações do usuário atual",
    description="Retorna os dados do usuário baseado no token fornecido."
)
async def get_current_user_info(
    current_user=Depends(get_current_user)
):
    """
    Retorna informações do usuário autenticado.
    
    Útil para:
    - Verificar se token é válido
    - Obter dados do usuário no frontend
    - Depuração
    """
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "role": current_user.role,
        "clinica_id": current_user.clinica_id,
        "ativo": current_user.ativo,
        "ultimo_login": current_user.ultimo_login.isoformat() if current_user.ultimo_login else None
    }
