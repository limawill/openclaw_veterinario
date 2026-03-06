from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ClinicaCreate(BaseModel):
    """
    Schema para CRIAR uma nova clínica.
    Cliente envia APENAS estes campos.
    """
    nome: str = Field(..., min_length=3, max_length=255, description="Nome da clínica")
    endereco: Optional[str] = Field(None, max_length=500, description="Endereço completo")
    configuracoes: Optional[Dict] = Field(default={}, description="Configurações em JSON")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Clínica Vet Saúde",
                "endereco": "Rua A, 123 - Centro",
                "configuracoes": {
                    "tempo_padrao_consulta": 30,
                    "dias_antecedencia": 60
                }
            }
        }


class ClinicaUpdate(BaseModel):
    """
    Schema para ATUALIZAR uma clínica.
    Todos os campos são opcionais (só envia o que quer mudar).
    """
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    endereco: Optional[str] = Field(None, max_length=500)
    configuracoes: Optional[Dict] = None
    ativo: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Clínica Vet Saúde (Matriz)",
                "endereco": "Av. Central, 456",
                "configuracoes": {"tempo_padrao": 40},
                "ativo": True
            }
        }


class ClinicaResponse(BaseModel):
    """Schema para RETORNAR dados de uma clínica."""
    id: str
    nome: str
    endereco: Optional[str]
    configuracoes: Optional[Dict]
    ativo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "nome": "Clínica Vet Saúde",
                "endereco": "Rua A, 123 - Centro",
                "configuracoes": {"tempo_padrao": 30},
                "ativo": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class ClinicaListResponse(BaseModel):
    """Schema para listagem de clínicas."""
    mensagem: str
    total: int
    clinicas: List[ClinicaResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "mensagem": "Encontradas 2 clínicas",
                "total": 2,
                "clinicas": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "nome": "Clínica Vet Saúde",
                        "endereco": "Rua A, 123",
                        "ativo": True
                    }
                ]
            }
        }