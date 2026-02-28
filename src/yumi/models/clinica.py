from datetime import datetime
from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, JSON


class Clinica(Base, TimestampMixin):
    """Representa uma clínica veterinária no sistema."""
    __tablename__ = 'clinica'

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    nome = Column(String(255), nullable=False)
    endereco = Column(String(500))
    configuracoes = Column(JSON) 
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    clinica_funcionamento = relationship("ClinicaFuncionamento", back_populates="clinica")
    integracao = relationship("Integracao", back_populates="clinica")
    agendamentos = relationship("Agendamento", back_populates="clinica")
