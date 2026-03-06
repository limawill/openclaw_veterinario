from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from yumi.utils.uuid_generator import gerar_uuid

from .base import Base, TimestampMixin


class Usuario(Base, TimestampMixin):
    """Representa usuários vinculados a uma clínica."""
    __tablename__ = 'usuario'
    
    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False) 
    role = Column(String(100), nullable=False)
    ultimo_login = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True)
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="usuarios")
