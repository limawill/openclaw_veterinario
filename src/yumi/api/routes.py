"""Rotas principais da API."""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from yumi.utils.system_info import get_project_info
from yumi.models.schemas import ProjectInfo, HealthCheck, ErrorResponse

# Criar router principal
router = APIRouter()

@router.get(
    "/",
    response_model=ProjectInfo,
    summary="Informações do Projeto",
    description="Retorna informações detalhadas sobre o projeto Yumi, incluindo versões e dependências.",
    responses={
        200: {"description": "Informações obtidas com sucesso"},
        500: {"description": "Erro interno", "model": ErrorResponse}
    }
)
async def root():
    """
    Endpoint raiz que retorna informações do projeto.
    
    Retorna:
    - Nome e descrição do projeto
    - Versão atual
    - Ambiente (dev/prod)
    - Versões do Python, OS e SQLite
    - Dependências principais
    - Timestamp da consulta
    """
    try:
        return get_project_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter informações: {str(e)}"
        )

@router.get(
    "/health",
    response_model=HealthCheck,
    summary="Health Check",
    description="Verifica se a API está funcionando corretamente."
)
async def health_check():
    """
    Endpoint para verificar saúde da aplicação.
    
    Retorna status 'ok' se tudo estiver funcionando.
    Útil para monitoramento e orquestração.
    """
    return HealthCheck(
        status="ok",
        timestamp=datetime.now(),
        database="conectado"  # Placeholder, depois implementaremos verificação real
    )

@router.get(
    "/info/python",
    summary="Informações do Python",
    description="Retorna apenas informações do Python."
)
async def python_info():
    """Endpoint específico para informações do Python."""
    from yumi.utils.system_info import get_python_version, get_python_version_short
    
    return {
        "versao_completa": get_python_version(),
        "versao": get_python_version_short(),
        "executavel": __import__('sys').executable
    }

@router.get(
    "/info/sqlite",
    summary="Informações do SQLite",
    description="Retorna a versão do SQLite em uso."
)
async def sqlite_info():
    """Endpoint específico para informações do SQLite."""
    from yumi.utils.system_info import get_sqlite_version
    
    return {
        "versao_sqlite": get_sqlite_version()
    }