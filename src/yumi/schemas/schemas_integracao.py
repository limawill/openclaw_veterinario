from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# =====================================================
# SCHEMAS PARA RECEBER DADOS (REQUEST)
# =====================================================


class IntegracaoBase(BaseModel):
    """Campos base para integração."""
    clinica_id: str = Field(..., description="ID da clínica")
    tipo_servico: str = Field(..., description="google_calendar, whatsapp, telegram, outlook")
    credenciais: Dict[str, Any] = Field(..., description="Tokens, webhooks, configurações")
    
    @validator('tipo_servico')
    def validar_tipo_servico(cls, v):
        """Valida se o tipo de serviço é suportado."""
        servicos_validos = ['google_calendar', 'whatsapp', 'telegram', 'outlook']
        if v not in servicos_validos:
            raise ValueError(f"Tipo de serviço deve ser um de: {', '.join(servicos_validos)}")
        return v


class IntegracaoCreate(IntegracaoBase):
    """Schema para CRIAR uma nova integração."""
    ativo: bool = Field(True, description="Começa ativa por padrão")


class IntegracaoUpdate(BaseModel):
    """Schema para ATUALIZAR uma integração (todos opcionais)."""
    tipo_servico: Optional[str] = Field(None, description="google_calendar, whatsapp, telegram")
    credenciais: Optional[Dict[str, Any]] = Field(None, description="Novas credenciais")
    ativo: Optional[bool] = Field(None, description="Ativar/desativar")
    
    @validator('tipo_servico')
    def validar_tipo_servico(cls, v):
        if v is not None:
            servicos_validos = ['google_calendar', 'whatsapp', 'telegram', 'outlook']
            if v not in servicos_validos:
                raise ValueError(f"Tipo de serviço deve ser um de: {', '.join(servicos_validos)}")
        return v

# =====================================================
# SCHEMAS ESPECÍFICOS POR TIPO DE INTEGRAÇÃO (OPCIONAL)
# =====================================================

class GoogleCalendarCredenciais(BaseModel):
    """Schema específico para credenciais do Google Calendar."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    calendar_id: str = Field("primary", description="ID do calendário")
    token_type: str = "Bearer"
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "ya29.a0AfH6S...",
                "refresh_token": "1//0g...",
                "expires_in": 3600,
                "calendar_id": "primary"
            }
        }

class WhatsAppCredenciais(BaseModel):
    """Schema específico para WhatsApp Business."""
    phone_number_id: str
    access_token: str
    webhook_url: Optional[str] = None
    webhook_token: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number_id": "123456789",
                "access_token": "EAA...",
                "webhook_url": "https://yumi.com/webhook/whatsapp"
            }
        }


class TelegramCredenciais(BaseModel):
    """Schema específico para Telegram."""
    bot_token: str
    chat_id: Optional[str] = None
    webhook_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "bot_token": "123456:ABC-DEF1234",
                "webhook_url": "https://yumi.com/webhook/telegram"
            }
        }

# =====================================================
# SCHEMAS PARA RESPOSTA (RESPONSE)
# =====================================================

class IntegracaoResponse(BaseModel):
    """Schema para RETORNAR dados de uma integração."""
    id: str
    clinica_id: str
    tipo_servico: str
    credenciais: Dict[str, Any]
    ativo: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Informações adicionais (opcional)
    nome_clinica: Optional[str] = Field(None, description="Nome da clínica (join)")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        json_schema_extra = {
            "example": {
                "id": "990e8400-e29b-41d4-a716-446655440004",
                "clinica_id": "550e8400-e29b-41d4-a716-446655440000",
                "tipo_servico": "google_calendar",
                "credenciais": {
                    "access_token": "ya29...",
                    "expires_in": 3600
                },
                "ativo": True,
                "created_at": "2024-01-15T12:00:00"
            }
        }

class IntegracaoListResponse(BaseModel):
    """Schema para listagem de integrações."""
    mensagem: str
    total: int
    integracoes: List[IntegracaoResponse]

# =====================================================
# SCHEMAS PARA AÇÕES ESPECÍFICAS
# =====================================================

class IntegracaoTesteRequest(BaseModel):
    """Schema para testar integração (pode enviar credenciais temporárias)."""
    credenciais_teste: Optional[Dict[str, Any]] = Field(None, description="Credenciais para teste")

class IntegracaoTesteResponse(BaseModel):
    """Schema para resposta do teste de integração."""
    sucesso: bool
    mensagem: str
    detalhes: Optional[Dict[str, Any]] = Field(None, description="Detalhes do teste")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sucesso": True,
                "mensagem": "Conexão com Google Calendar estabelecida",
                "detalhes": {
                    "calendar_name": "Agenda da Clínica",
                    "email": "clinica@gmail.com"
                }
            }
        }