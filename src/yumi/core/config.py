from pydantic import ConfigDict
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    ###########################################
    #         CONFIGURAÇÕES DA API            #
    ###########################################
    APP_NAME: str = "Yumi Agent"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Agente virtual para clínica veterinária"
    ENVIRONMENT: str = "development"
    
    ###########################################
    #           SERVIDOR UVICORN              #
    ###########################################
    HOST: str = "0.0.0.0"
    PORT: int = 9100
    RELOAD: bool = True
    
    ###########################################
    #              BANCO DE DADOS             #
    ###########################################
    DATABASE_URL: str = "sqlite:///./src/yumi/database/yumi.db"
    DATABASE_ECHO: bool = False
    
    ###########################################
    #                SEGURANÇA                 #
    ###########################################
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()

# Instância global para uso fácil
settings = get_settings()
