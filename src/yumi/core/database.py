import sqlite3
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from yumi.core.config import settings
from yumi.core.logger import logger

# 1. Cria a engine (conexão com o banco)
#    - connect_args: só para SQLite (ignorado em outros bancos)
logger.info(f"Inicializando conexão com banco de dados: {settings.DATABASE_URL}")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DATABASE_ECHO
)

logger.debug("Engine criada com sucesso")

# 2. Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Dependência do FastAPI para obter a sessão
def get_db():
    """
    Dependência que fornece uma sessão de banco de dados.
    Uso: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    logger.debug("Nova sessão de banco de dados aberta")
    try:
        yield db
    except Exception:
        logger.error("Erro durante operação de banco de dados", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Sessão de banco de dados fechada")


# 4. Utilitários para acesso direto ao SQLite (usado pelo init_db.py)

def get_db_path_from_url() -> Path:
    """
    Extrai o caminho do arquivo .db a partir da DATABASE_URL.

    Exemplo:
        'sqlite:///./src/yumi/database/yumi.db'  →  Path('src/yumi/database/yumi.db')

    Funciona apenas com SQLite. Para Postgres/MySQL, o init_db deve ser
    adaptado para usar migrations (Alembic).
    """
    url = settings.DATABASE_URL
    if not url.startswith("sqlite"):
        raise RuntimeError(
            "get_db_path_from_url() só funciona com SQLite. "
            "Para outros bancos use Alembic para gerenciar o schema."
        )
    # Remove o prefixo 'sqlite:///' e normaliza para Path absoluto
    raw_path = url.replace("sqlite:///", "")
    return Path(raw_path).resolve()


def get_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão sqlite3 pura (sem SQLAlchemy).

    Usado pelo init_db.py para executar o models.sql via executescript(),
    que não é suportado pelo SQLAlchemy diretamente.
    """
    db_path = get_db_path_from_url()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn