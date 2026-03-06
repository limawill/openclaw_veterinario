from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from yumi.core.config import settings

# =====================================================
# CONTEXTO DE HASH (BCRYPT)
# =====================================================

# Cria um contexto para gerenciar hash de senhas
# - bcrypt é o algoritmo recomendado
# - deprecated="auto" atualiza automaticamente hashes antigos
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha: str) -> str:
    """
    Gera um hash seguro da senha usando bcrypt.
    
    Args:
        senha: string com a senha em texto puro
        
    Returns:
        string com o hash da senha
        
    Exemplo:
        >>> hash = gerar_hash_senha("minha_senha123")
        >>> print(hash)
        $2b$12$KIXZQ7xKIXZQ7xKIXZQ7xO...
    """
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """
    Verifica se a senha corresponde ao hash armazenado.
    
    Args:
        senha: string com a senha em texto puro (tentativa)
        hash_armazenado: hash salvo no banco
        
    Returns:
        True se a senha estiver correta, False caso contrário
        
    Exemplo:
        >>> hash = "$2b$12$KIXZQ7xKIXZQ7xKIXZQ7xO..."
        >>> verificar_senha("minha_senha123", hash)
        True
        >>> verificar_senha("senha_errada", hash)
        False
    """
    return pwd_context.verify(senha, hash_armazenado)

# =====================================================
# CRIAÇÃO E VERIFICAÇÃO DE JWT
# =====================================================

def criar_token_jwt(dados: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos.
    
    Args:
        dados: dicionário com os dados que vão no payload
        expires_delta: tempo de expiração (opcional)
        
    Returns:
        string com o token JWT
        
    Exemplo:
        >>> payload = {"sub": "user123", "role": "admin"}
        >>> token = criar_token_jwt(payload)
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    # Cria uma cópia para não modificar o original
    payload = dados.copy()
    
    # Define expiração
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Adiciona expiração ao payload
    payload.update({"exp": expire})
    
    # Cria o token
    token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return token

def criar_refresh_token(dados: Dict[str, Any]) -> str:
    """
    Cria um refresh token JWT de longa duração.

    Diferenças em relação ao access token:
    - Validade maior (REFRESH_TOKEN_EXPIRE_DAYS, padrão 7 dias)
    - Contém o campo "type": "refresh" para distinguir dos access tokens
    - Payload mínimo: apenas sub, clinica_id e role (sem dados extras)

    Args:
        dados: dicionário com sub, clinica_id e role do usuário

    Returns:
        string com o refresh token JWT
    """
    payload = dados.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload.update({"exp": expire, "type": "refresh"})

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token_jwt(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: string com o token JWT
        
    Returns:
        dicionário com o payload do token
        
    Raises:
        JWTError: se o token for inválido ou expirado
        
    Exemplo:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decodificar_token_jwt(token)
        >>> print(payload["sub"])
        user123
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        # Relança a exceção para ser tratada em camadas superiores
        raise JWTError(f"Token inválido: {str(e)}")

# =====================================================
# FUNÇÕES AUXILIARES (OPCIONAL)
# =====================================================

def extrair_dados_usuario_do_token(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai e valida os dados do usuário do payload do token.
    
    Args:
        payload: payload decodificado do token
        
    Returns:
        dicionário com id, clinica_id e role
        
    Raises:
        ValueError: se faltar campos obrigatórios
    """
    user_id = payload.get("sub")
    clinica_id = payload.get("clinica_id")
    role = payload.get("role")
    
    if not user_id or not clinica_id or not role:
        raise ValueError("Token não contém dados completos do usuário")
    
    return {
        "id": user_id,
        "clinica_id": clinica_id,
        "role": role
    }