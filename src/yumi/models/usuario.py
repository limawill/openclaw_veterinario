from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy import Column, String, Boolean, ForeignKey


class Usuario(Base, TimestampMixin):
    """Representa usuários vinculados a uma clínica."""
    __tablename__ = 'usuario'
    
    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(100), nullable=False)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="usuarios")
