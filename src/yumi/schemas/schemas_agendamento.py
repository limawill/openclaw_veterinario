from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# =====================================================
# SCHEMAS PARA RECEBER DADOS (REQUEST)
# =====================================================

class AgendamentoBase(BaseModel):
    """Campos base para agendamento."""
    clinica_id: str = Field(..., description="ID da clínica")
    veterinario_id: str = Field(..., description="ID do veterinário")
    nome_cliente: str = Field(..., min_length=3, max_length=255)
    telefone_cliente: Optional[str] = Field(None, max_length=20)
    nome_pet: str = Field(..., min_length=1, max_length=255)
    data_hora_inicio: datetime
    data_hora_fim: datetime
    origem: str = Field(..., description="chatbot, manual, whatsapp, telegram")

class AgendamentoCreate(AgendamentoBase):
    """Schema para CRIAR um agendamento."""
    status: str = Field("agendado", description="agendado, confirmado, cancelado, concluido")
    id_evento_externo: Optional[str] = None

class AgendamentoUpdate(BaseModel):
    """Schema para ATUALIZAR um agendamento (todos opcionais)."""
    veterinario_id: Optional[str] = None
    nome_cliente: Optional[str] = Field(None, min_length=3, max_length=255)
    telefone_cliente: Optional[str] = Field(None, max_length=20)
    nome_pet: Optional[str] = Field(None, min_length=1, max_length=255)
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    status: Optional[str] = None
    origem: Optional[str] = None

# =====================================================
# SCHEMAS PARA RESPOSTA (RESPONSE)
# =====================================================

class AgendamentoResponse(BaseModel):
    """Schema para RETORNAR dados de um agendamento."""
    id: str
    clinica_id: str
    veterinario_id: str
    nome_cliente: str
    telefone_cliente: Optional[str]
    nome_pet: str
    data_hora_inicio: datetime
    data_hora_fim: datetime
    status: str
    origem: str
    id_evento_externo: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Campos adicionais para enriquecer a resposta (opcional)
    nome_veterinario: Optional[str] = Field(None, description="Nome do veterinário (join)")
    nome_clinica: Optional[str] = Field(None, description="Nome da clínica (join)")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class AgendamentoListResponse(BaseModel):
    """Schema para listagem de agendamentos."""
    mensagem: str
    total: int
    agendamentos: List[AgendamentoResponse]