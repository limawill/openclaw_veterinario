import sqlite3
from pathlib import Path
from yumi.core.config import settings


def get_db_path_from_url() -> Path:
    """
    Extrai o caminho do arquivo da DATABASE_URL.
    Funciona com sqlite:///caminho/para/arquivo.db
    """
    if not settings.DATABASE_URL.startswith("sqlite:///"):
        raise ValueError(f"Banco não é SQLite: {settings.DATABASE_URL}")
    
    # Remove 'sqlite:///' e pega o caminho
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    # Se for caminho relativo, resolve a partir da raiz do projeto
    if not Path(db_path).is_absolute():
        # Sobe de core/ até a raiz do projeto
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / db_path
    
    return Path(db_path)


def get_connection():
    """Retorna uma conexão com o banco SQLite."""
    db_path = get_db_path_from_url()
    
    # Garante que o diretório existe
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
