from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from yumi.models.base import Base


class RefreshToken(Base):
    """
    Model para armazenar refresh tokens emitidos.

    Por que guardar no banco?
    - Permite invalidar um token antes do vencimento (logout real)
    - Detecta reutilização de token (segurança extra)
    - Rastreia quantas sessões um usuário tem abertas

    Campos:
        id          — UUID do registro
        usuario_id  — FK para o usuário dono do token
        token       — O JWT do refresh token (valor completo)
        expires_at  — Quando o token vence (sincronizado com o JWT)
        revogado    — True quando o logout foi chamado
        created_at  — Quando a sessão foi iniciada (login)
    """

    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, nullable=False)
    usuario_id = Column(
        String(36),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return (
            f"<RefreshToken usuario_id={self.usuario_id!r} "
            f"revogado={self.revogado} expires_at={self.expires_at!r}>"
        )
