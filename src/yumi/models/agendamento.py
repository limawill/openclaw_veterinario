from .base import Base, TimestampMixin
from sqlalchemy.orm import relationship
from yumi.utils.uuid_generator import gerar_uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint


class Agendamento(Base, TimestampMixin):
    """Representa um agendamento de consulta veterinária."""
    __tablename__ = "agendamento"
    
    __table_args__ = (
        CheckConstraint('data_hora_fim > data_hora_inicio', name='check_horario_valido'),
    )

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(String(36), ForeignKey('clinica.id'), nullable=False)
    veterinario_id = Column(String(36), ForeignKey('veterinario.id'), nullable=False)
    
    nome_cliente = Column(String(255), nullable=False)
    telefone_cliente = Column(String(20))
    nome_pet = Column(String(255))
    
    data_hora_inicio = Column(DateTime, nullable=False)
    data_hora_fim = Column(DateTime, nullable=False)
    
    status = Column(String(50), nullable=False, default='agendado')  # agendado, confirmado, cancelado, concluido
    origem = Column(String(50), nullable=False)  # chatbot, manual, whatsapp, telegram
    
    id_evento_externo = Column(String(255))  # ID no Google Calendar
    
    # Relacionamentos
    clinica = relationship("Clinica", back_populates="agendamentos")
    veterinario = relationship("Veterinario", back_populates="agendamentos")
