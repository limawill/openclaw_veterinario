from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

# =====================================================
# SCHEMAS PARA RECEBER DADOS (REQUEST)
# =====================================================

class ClinicaFuncionamentoBase(BaseModel):
    """Campos base para funcionamento (reutilizado em criação/atualização)."""
    dia_semana: int = Field(..., ge=0, le=6, description="0=Dom, 1=Seg, ..., 6=Sáb")
    hora_abertura: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Formato HH:MM")
    hora_fechamento: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Formato HH:MM")
    
    @validator('hora_fechamento')
    def validar_horario(cls, v, values):
        """Valida se hora_fechamento > hora_abertura"""
        if 'hora_abertura' in values and v <= values['hora_abertura']:
            raise ValueError('hora_fechamento deve ser maior que hora_abertura')
        return v

class ClinicaFuncionamentoCreate(ClinicaFuncionamentoBase):
    """Schema para CRIAR um horário de funcionamento."""
    pass  # Herda todos os campos do base

class ClinicaFuncionamentoUpdate(BaseModel):
    """Schema para ATUALIZAR um horário (todos opcionais)."""
    dia_semana: Optional[int] = Field(None, ge=0, le=6)
    hora_abertura: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_fechamento: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")

# =====================================================
# SCHEMAS PARA RESPOSTA (RESPONSE)
# =====================================================

class ClinicaFuncionamentoResponse(ClinicaFuncionamentoBase):
    """Schema para RETORNAR dados de um horário."""
    id: str
    clinica_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class ClinicaFuncionamentoListResponse(BaseModel):
    """Schema para listagem de horários."""
    mensagem: str
    total: int
    horarios: List[ClinicaFuncionamentoResponse]