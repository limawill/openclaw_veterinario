"""
chat.py — Modelos ORM para sessões e mensagens de conversa.

Tabelas mapeadas (já existentes no banco via models.sql):
    - chat_sessions  : uma sessão por conversa (multi-canal, multi-tenant)
    - chat_messages  : mensagens individuais dentro de uma sessão

Por que NOT usar TimestampMixin aqui?
    Estas tabelas têm apenas created_at (imutáveis por design).
    Mensagens não são editadas — só inseridas e lidas.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from yumi.utils.uuid_generator import gerar_uuid

from .base import Base


class ChatSession(Base):
    """
    Representa uma sessão de conversa entre um usuário e o Yumi Agent.

    Uma sessão agrupa mensagens relacionadas a uma mesma interação.
    Isolamento multi-tenant garantido via clinica_id.
    """

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    clinica_id = Column(
        String(36),
        ForeignKey("clinica.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canal = Column(String(100), nullable=False, default="chat")
    usuario_id = Column(
        String(36),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamento: uma sessão tem muitas mensagens
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatSession id={self.id} canal={self.canal} clinica={self.clinica_id}>"


class ChatMessage(Base):
    """
    Representa uma mensagem individual dentro de uma sessão de conversa.

    role: "user" → mensagem enviada pelo usuário
          "assistant" → resposta gerada pelo Yumi Agent
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_message_role"),
    )

    id = Column(String(36), primary_key=True, default=gerar_uuid)
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relacionamento inverso
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ChatMessage id={self.id} role={self.role} session={self.session_id}>"
