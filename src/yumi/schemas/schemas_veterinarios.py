from typing import Optional

from pydantic import BaseModel, Field


class VeterinarioCreate(BaseModel):
    """
    Schema para CRIAR um novo veterinário.
    Cliente envia APENAS estes campos.
    """
    clinica_id: str = Field(..., min_length=36, max_length=36, description="ID da clínica associada")
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo do veterinário")
    especialidade: str = Field(..., max_length=255, description="Especialidade do veterinário")
    email: str = Field(..., max_length=255, description="Email do veterinário")
    ativo: bool = Field(default=True, description="Indica se o veterinário está ativo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "clinica_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "nome": "João Silva",
                "especialidade": "Cardiologia",
                "email": "joao.silva@clinica.com",
                "ativo": True
            }
        }


class VeterinarioUpdate(BaseModel):
    """
    Schema para ATUALIZAR um veterinário.
    Todos os campos são opcionais (só envia o que quer mudar).
    """
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    especialidade: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    ativo: Optional[bool] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "especialidade": "Cardiologia",
                "email": "joao.silva@clinica.com",
                "ativo": True
            }
        }
