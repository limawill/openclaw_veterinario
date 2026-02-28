from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from yumi.core.config import settings

# 1. Cria a engine (conexão com o banco)
#    - connect_args: só para SQLite (ignorado em outros bancos)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DATABASE_ECHO
)

# 2. Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Dependência do FastAPI para obter a sessão
def get_db():
    """
    Dependência que fornece uma sessão de banco de dados.
    Uso: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()