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
    except Exception as e:
        logger.error("Erro durante operação de banco de dados", exception=e)
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Sessão de banco de dados fechada")