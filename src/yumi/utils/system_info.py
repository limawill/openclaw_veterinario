"""Utilitários para informações do sistema e projeto."""

import sys
import platform
import sqlite3
from datetime import datetime
from importlib.metadata import version, distributions

def get_python_version() -> str:
    """Retorna a versão do Python em uso."""
    return sys.version

def get_python_version_short() -> str:
    """Retorna a versão curta do Python."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def get_os_info() -> str:
    """Retorna informações do sistema operacional."""
    return f"{platform.system()} {platform.release()}"

def get_sqlite_version() -> str:
    """Retorna a versão do SQLite."""
    return sqlite3.sqlite_version

def get_project_dependencies() -> dict:
    """Retorna dicionário com dependências principais e suas versões."""
    deps = {}
    main_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
    
    for package in main_packages:
        try:
            deps[package] = version(package)
        except Exception:
            deps[package] = "não instalado"
    
    return deps

def get_all_dependencies() -> list:
    """Retorna lista de todas as dependências instaladas."""
    return [f"{dist.metadata['Name']}=={dist.version}" 
            for dist in distributions()]

def get_project_info() -> dict:
    """Retorna informações completas do projeto."""
    return {
        "nome": "Yumi Agent",
        "descricao": "Agente virtual para clínica veterinária",
        "versao": "0.1.0",
        "ambiente": "desenvolvimento",
        "python": get_python_version_short(),
        "os": get_os_info(),
        "sqlite": get_sqlite_version(),
        "timestamp": datetime.now().isoformat(),
        "dependencias": get_project_dependencies()
    }