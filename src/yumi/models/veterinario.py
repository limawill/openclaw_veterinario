from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy import Column, String, Boolean, ForeignKey


class Veterinario(Base, TimestampMixin):
    """Representa profissionais veterinários vinculados à clínica."""
    __tablename__ = 'veterinario'
    
    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    nome = Column(String(255), nullable=False)
    especialidade = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="veterinarios")
    agendamentos = relationship("Agendamento", back_populates="veterinario")
