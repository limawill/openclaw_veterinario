from typing import Optional

from pydantic import BaseModel, Field, model_validator


class UsuarioCreate(BaseModel):
    """
    Schema para CRIAR um novo usuário.
    Cliente envia APENAS estes campos.
    """
    clinica_id: str = Field(..., min_length=36, max_length=36, description="ID da clínica associada")
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo do usuário")
    email: str = Field(..., max_length=255, description="Email do usuário")
    role: str = Field(..., description="Papel do usuário: admin, dev ou atendente")
    ativo: bool = Field(default=True, description="Indica se o usuário está ativo")

    @model_validator(mode="after")
    def validate_role(self):
        """Valida se o role é um dos valores permitidos."""
        if self.role not in ('admin', 'dev', 'atendente'):
            raise ValueError(
                f"Role inválido: {self.role!r}. "
                f"Valores aceitos: 'admin', 'dev', 'atendente'"
            )
        return self

    @model_validator(mode="after")
    def normalize_ativo(self):
        if self.ativo is not None:
            self.ativo = self.ativo
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "clinica_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "nome": "João Silva",
                "email": "joao.silva@example.com",
                "role": "admin",
                "ativo": True
            }
        }


class UsuarioUpdate(BaseModel):
    """
    Schema para ATUALIZAR um usuário.
    Todos os campos são opcionais (só envia o que quer mudar).
    """
    nome: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None)
    ativo: Optional[bool] = Field(default=None)

    @model_validator(mode="after")
    def validate_role(self):
        """Valida se o role é um dos valores permitidos."""
        if self.role is not None and self.role not in ('admin', 'dev', 'atendente'):
            raise ValueError(
                f"Role inválido: {self.role!r}. "
                f"Valores aceitos: 'admin', 'dev', 'atendente'"
            )
        return self

    @model_validator(mode="after")
    def normalize_ativo(self):
        if self.ativo is not None:
            self.ativo = self.ativo
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "email": "joao.silva@example.com",
                "role": "dev",
                "ativo": True
            }
        }
