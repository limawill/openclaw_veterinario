from typing import Dict, Optional

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