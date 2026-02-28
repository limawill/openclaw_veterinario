from sqlalchemy import JSON, Boolean, Column, String
from sqlalchemy.orm import relationship

from yumi.utils.uuid_generator import gerar_uuid

from .base import Base, TimestampMixin


class Clinica(Base, TimestampMixin):
    """Representa uma clínica veterinária no sistema."""
    __tablename__ = 'clinica'

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    nome = Column(String(255), nullable=False)
    endereco = Column(String(500))
    configuracoes = Column(JSON) 
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="clinica")
    veterinarios = relationship("Veterinario", back_populates="clinica")
    clinica_funcionamento = relationship("ClinicaFuncionamento", back_populates="clinica")
    integracao = relationship("Integracao", back_populates="clinica")
    agendamentos = relationship("Agendamento", back_populates="clinica")
