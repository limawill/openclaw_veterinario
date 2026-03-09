"""Pacote com modelos ORM e schemas de dados da aplicação."""

from .agendamento import Agendamento
from .base import Base, TimestampMixin
from .chat import ChatMessage, ChatSession
from .clinica import Clinica
from .clinica_funcionamento import ClinicaFuncionamento
from .integracao import Integracao
from .refresh_token import RefreshToken
from .usuario import Usuario
from .veterinario import Veterinario

__all__ = [
    "Base",
    "TimestampMixin",
    "Clinica",
    "ClinicaFuncionamento",
    "Usuario",
    "Veterinario",
    "Agendamento",
    "Integracao",
    "RefreshToken",
    "ChatSession",
    "ChatMessage",
]
