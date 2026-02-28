from datetime import datetime
from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey


class ClinicaFuncionamento(Base, TimestampMixin):
    """Armazena horários de funcionamento por dia da semana."""
    __tablename__ = 'clinica_funcionamento'

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    dia_semana = Column(Integer, nullable=False)
    hora_abertura = Column(String(5), nullable=False)
    hora_fechamento = Column(String(5), nullable=False)
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="clinica_funcionamento")
