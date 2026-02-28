from datetime import datetime
from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean,JSON, ForeignKey


class Integracao(Base, TimestampMixin):
    """Representa uma integração ativa de uma clínica com serviços externos."""
    __tablename__ = 'integracao'

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    tipo_servico = Column(String(50), nullable=False)  # Ex: "google_calendar", "outlook", etc.
    credenciais = Column(JSON, nullable=False)  # Armazena as configuraçes específicas da integração
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="integracao")

