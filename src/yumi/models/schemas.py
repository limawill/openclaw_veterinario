"""Schemas Pydantic para validação e documentação das respostas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class ProjectInfo(BaseModel):
    """Schema para informações do projeto."""
    nome: str
    descricao: str
    versao: str
    ambiente: str
    python: str
    os: str
    sqlite: str
    timestamp: datetime
    dependencias: Dict[str, str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Yumi Agent",
                "descricao": "Agente virtual para clínica veterinária",
                "versao": "0.1.0",
                "ambiente": "desenvolvimento",
                "python": "3.12.5",
                "os": "Linux 6.5.0",
                "sqlite": "3.42.0",
                "timestamp": "2024-01-20T10:30:00",
                "dependencias": {
                    "fastapi": "0.115.0",
                    "uvicorn": "0.30.0",
                    "sqlalchemy": "2.0.0"
                }
            }
        }

class HealthCheck(BaseModel):
    """Schema para health check."""
    status: str
    timestamp: datetime
    database: Optional[str] = None
    
class ErrorResponse(BaseModel):
    """Schema para respostas de erro."""
    detail: str
    timestamp: datetime