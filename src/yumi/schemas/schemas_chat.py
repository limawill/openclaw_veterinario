"""
schemas_chat.py — Schemas Pydantic para o endpoint de chat do Yumi Agent.

Domínio: mensagens trocadas entre o cliente e o agente Yumi.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Requisição ao endpoint POST /api/v1/agent/chat."""

    clinica_id: str = Field(
        ...,
        description="ID da clínica. Deve corresponder ao clinica_id do token JWT.",
        example="170a7399-4b47-4ad1-a10b-a8ac69b4a166",
    )
    mensagem: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Mensagem enviada pelo usuário ao agente.",
        example="Quero agendar uma consulta para amanhã",
    )
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "ID da sessão de conversa existente. "
            "Se ausente ou None, uma nova sessão é criada automaticamente."
        ),
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    )


class ChatResponse(BaseModel):
    """Resposta do endpoint POST /api/v1/agent/chat."""

    intencao: str = Field(
        description="Intenção detectada pelo agente.",
        example="agendar_consulta",
    )
    resposta: str = Field(
        description="Texto de resposta gerado pelo agente para o usuário.",
        example="Claro! Temos os seguintes veterinários disponíveis...",
    )
    dados: dict[str, Any] | None = Field(
        default=None,
        description="Dados estruturados extras retornados pelo agente (para uso do frontend).",
    )
    session_id: str = Field(
        description=(
            "ID da sessão de conversa usada (nova ou existente). "
            "O frontend deve armazenar e reenviar este ID para manter o histórico."
        ),
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    )
