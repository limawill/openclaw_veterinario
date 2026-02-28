"""Pacote com modelos ORM e schemas de dados da aplicação."""

from .clinica import Clinica
from .clinica_funcionamento import ClinicaFuncionamento
from .usuario import Usuario
from .veterinario import Veterinario
from .agendamento import Agendamento
from .integracao import Integracao
from .base import Base, TimestampMixin

__all__ = [
    "Base",
    "TimestampMixin",
    "Clinica",
    "ClinicaFuncionamento",
    "Usuario",
    "Veterinario",
    "Agendamento",
    "Integracao",
]
