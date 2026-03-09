"""
chat_service.py — Camada de acesso ao banco para sessões e mensagens de chat.

Responsabilidade única: persistência e recuperação de dados de conversa.
Sem lógica de negócio — isso fica no YumiAgent.

Funções públicas:
    get_or_create_session  — obtém sessão existente ou cria uma nova
    save_message           — persiste uma mensagem (user ou assistant)
    get_history            — recupera as últimas N mensagens da sessão
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from yumi.core.logger import logger
from yumi.models.chat import ChatMessage, ChatSession
from yumi.utils.uuid_generator import gerar_uuid


def get_or_create_session(
    db: Session,
    clinica_id: str,
    usuario_id: str,
    session_id: str | None = None,
    canal: str = "chat",
) -> ChatSession:
    """
    Retorna sessão existente (se session_id fornecido) ou cria uma nova.

    Args:
        db:           Sessão do banco de dados.
        clinica_id:   ID da clínica — garante isolamento multi-tenant.
        usuario_id:   ID do usuário autenticado que iniciou a conversa.
        session_id:   ID de sessão existente. Se None, cria nova sessão.
        canal:        Canal de origem da conversa (padrão: "chat").

    Returns:
        ChatSession: objeto da sessão (existente ou recém-criada).

    Raises:
        HTTPException 404: se session_id fornecido não existir ou não pertencer
                           à clínica informada (prevenção de acesso cruzado).
    """
    if session_id:
        session = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.clinica_id == clinica_id,
            )
            .first()
        )
        if not session:
            logger.warning(
                f"[chat_service] Sessão '{session_id}' não encontrada "
                f"para clinica_id={clinica_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão '{session_id}' não encontrada para esta clínica.",
            )
        logger.debug(f"[chat_service] Sessão existente reutilizada: {session.id}")
        return session

    # Cria nova sessão (UUID gerado explicitamente para garantir o valor mesmo em testes)
    new_session = ChatSession(
        id=gerar_uuid(),
        clinica_id=clinica_id,
        usuario_id=usuario_id,
        canal=canal,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info(f"[chat_service] Nova sessão criada: {new_session.id} | canal={canal}")
    return new_session


def save_message(
    db: Session,
    session_id: str,
    role: str,
    message: str,
) -> ChatMessage:
    """
    Persiste uma mensagem na sessão de conversa.

    Args:
        db:         Sessão do banco de dados.
        session_id: ID da sessão à qual a mensagem pertence.
        role:       "user" para mensagem do usuário, "assistant" para resposta do agente.
        message:    Conteúdo textual da mensagem.

    Returns:
        ChatMessage: objeto persistido.
    """
    msg = ChatMessage(
        id=gerar_uuid(),
        session_id=session_id,
        role=role,
        message=message,
    )
    db.add(msg)
    db.commit()
    logger.debug(f"[chat_service] Mensagem salva — role={role} | session={session_id}")
    return msg


def get_history(
    db: Session,
    session_id: str,
    limit: int = 20,
) -> list[dict]:
    """
    Recupera as últimas N mensagens de uma sessão em ordem cronológica.

    Estratégia:
        1. Busca as <limit> mensagens mais recentes (ORDER BY created_at DESC, id DESC)
        2. Inverte a lista para retornar em ordem cronológica (mais antiga primeiro)

    A ordenação dupla (created_at + id) é determinística: se duas mensagens tiverem
    o mesmo timestamp, o id (UUID gerado sequencialmente) desempata.

    Isso garante que o histórico passado ao agente esteja na ordem correta
    para construir o contexto da conversa.

    Args:
        db:         Sessão do banco de dados.
        session_id: ID da sessão.
        limit:      Número máximo de mensagens a recuperar (padrão: 20).

    Returns:
        Lista de dicts: [{"role": "user"|"assistant", "message": "..."}]
        Lista vazia se a sessão não tiver mensagens.
    """
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    history = [{"role": m.role, "message": m.message} for m in reversed(msgs)]
    logger.debug(
        f"[chat_service] Histórico recuperado — session={session_id} | {len(history)} msgs"
    )
    return history
