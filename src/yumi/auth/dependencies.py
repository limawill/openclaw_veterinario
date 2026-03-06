from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from yumi.auth.auth_service import obter_usuario_por_id
from yumi.auth.security import decodificar_token_jwt
from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.models.usuario import Usuario

# =====================================================
# CONFIGURAÇÃO DO OAuth2
# =====================================================

# Cria uma instância do esquema OAuth2 com o nosso endpoint de login
# Isso faz o Swagger mostrar um botão "Authorize" automaticamente
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# =====================================================
# FUNÇÃO PRINCIPAL - OBTÉM USUÁRIO ATUAL DO TOKEN
# =====================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Valida o token JWT e retorna o usuário atual.
    
    Esta é a dependência BASE que todas as rotas protegidas vão usar.
    
    Args:
        token: Token JWT extraído do header Authorization
        db: Sessão do banco de dados
        
    Returns:
        Usuario: Objeto do usuário autenticado
        
    Raises:
        HTTPException 401 se token inválido ou usuário não encontrado
        HTTPException 403 se usuário inativo
    """
    logger.debug("Validando token de acesso")
    
    try:
        # 1. Decodifica o token
        payload = decodificar_token_jwt(token)
        usuario_id = payload.get("sub")
        
        if usuario_id is None:
            logger.warning("Token não contém 'sub' (ID do usuário)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. Busca o usuário no banco
        usuario = obter_usuario_por_id(db, usuario_id)
        
        # 3. Verifica se o usuário ainda está ativo
        if not usuario.ativo:
            logger.warning(f"Usuário inativo tentou acessar: {usuario.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo. Contate o administrador."
            )
        
        logger.debug(f"Usuário autenticado: {usuario.email} (role: {usuario.role})")
        return usuario
        
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# =====================================================
# DEPENDÊNCIAS DE AUTORIZAÇÃO (RBAC)
# =====================================================

async def get_current_admin(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependência para rotas que exigem role 'admin'.
    
    Uso:
        @router.get("/admin-only")
        async def rota_admin(admin: Usuario = Depends(get_current_admin)):
            ...
    """
    if current_user.role not in ["admin", "dev"]:  # dev também tem acesso admin
        logger.warning(
            f"Tentativa de acesso admin negado para {current_user.email} "
            f"(role: {current_user.role})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de administrador."
        )
    
    return current_user

async def get_current_atendente(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependência para rotas que exigem role 'atendente' ou superior.
    
    Acesso permitido para: atendente, admin, dev
    """
    roles_permitidas = ["atendente", "admin", "dev"]
    
    if current_user.role not in roles_permitidas:
        logger.warning(
            f"Tentativa de acesso atendente negado para {current_user.email} "
            f"(role: {current_user.role})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de atendente."
        )
    
    return current_user

async def get_current_dev(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependência para rotas que exigem role 'dev' (debug, ferramentas internas).
    """
    if current_user.role != "dev":
        logger.warning(
            f"Tentativa de acesso dev negado para {current_user.email} "
            f"(role: {current_user.role})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de desenvolvedor."
        )
    
    return current_user

# =====================================================
# DEPENDÊNCIA DE MULTI-TENANT (VERIFICAÇÃO DE CLÍNICA)
# =====================================================

async def verificar_mesma_clinica(
    clinica_id: str,
    current_user: Usuario = Depends(get_current_user)
) -> None:
    """
    Verifica se o clinica_id do usuário corresponde ao clinica_id da requisição.
    
    Útil para rotas que recebem clinica_id como parâmetro na URL.
    
    Exemplo:
        @router.get("/clinicas/{clinica_id}/dados")
        async def get_dados(
            clinica_id: str,
            _: None = Depends(verificar_mesma_clinica)  # ← validação
        ):
            ...
    """
    if current_user.clinica_id != clinica_id:
        logger.warning(
            f"Tentativa de acesso cruzado: usuário {current_user.email} "
            f"(clínica {current_user.clinica_id}) tentou acessar clínica {clinica_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a dados de outra clínica"
        )

# =====================================================
# FUNÇÃO AUXILIAR PARA OBTER APENAS O CLINICA_ID (OPCIONAL)
# =====================================================

async def get_current_clinica_id(
    current_user: Usuario = Depends(get_current_user)
) -> str:
    """
    Retorna apenas o ID da clínica do usuário atual.
    Útil para queries que precisam filtrar por clinica_id.
    """
    return current_user.clinica_id