"""
chat_service.py — Camada de acesso ao banco para sessões e mensagens de chat.

Responsabilidade única: persistência e recuperação de dados de conversa.
Sem lógica de negócio — isso fica no YumiAgent.

Funções públicas:
    get_or_create_session  — obtém sessão existente ou cria uma nova
    save_message           — persiste uma mensagem (user ou assistant)
    get_history            — recupera as últimas N mensagens da sessão
    process_chat_message   — orquestra OpenClaw + fallback local
"""

import json
import time
from collections.abc import AsyncGenerator, Callable
from typing import Any, TypedDict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from websockets.exceptions import ConnectionClosed, WebSocketException

from yumi.agents.yumi_agent.yumi import YumiAgent
from yumi.core.config import settings
from yumi.core.logger import logger
from yumi.core.metrics import (
    record_chat_latency,
    record_chat_request,
    record_openclaw_error,
    record_openclaw_fallback,
    record_openclaw_success,
    record_response_size,
    record_stream_duration,
    record_stream_request,
)
from yumi.models.chat import ChatMessage, ChatSession
from yumi.services.openclaw_client import OpenClawClient
from yumi.utils.uuid_generator import gerar_uuid


class ChatResult(TypedDict):
    """Payload de resposta retornado pela orquestração do chat."""

    intencao: str
    resposta: str
    dados: dict[str, Any] | None
    session_id: str


AgentFactory = Callable[..., Any]


_openclaw_client: OpenClawClient | None = None


def get_openclaw_client() -> OpenClawClient:
    """Retorna cliente OpenClaw singleton para reuso entre requests."""
    global _openclaw_client

    if _openclaw_client is None:
        _openclaw_client = OpenClawClient()

    return _openclaw_client


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
                "[chat_service] Sessão '%s' não encontrada para "
                "clinica_id=%s",
                session_id,
                clinica_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Sessão '{session_id}' não encontrada para esta "
                    "clínica."
                ),
            )
        logger.debug(
            "[chat_service] Sessão existente reutilizada: %s",
            session.id,
        )
        return session

    # Cria nova sessão com UUID explícito para previsibilidade em testes.
    new_session = ChatSession(
        id=gerar_uuid(),
        clinica_id=clinica_id,
        usuario_id=usuario_id,
        canal=canal,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info(
        "[chat_service] Nova sessão criada: %s | canal=%s",
        new_session.id,
        canal,
    )
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
        role:       "user" para mensagem do usuário.
                "assistant" para resposta do agente.
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
    logger.debug(
        "[chat_service] Mensagem salva — role=%s | session=%s",
        role,
        session_id,
    )
    return msg


def get_history(
    db: Session,
    session_id: str,
    limit: int = 20,
) -> list[dict]:
    """
    Recupera as últimas N mensagens de uma sessão em ordem cronológica.

    Estratégia:
          1. Busca as <limit> mensagens mais recentes.
              ORDER BY created_at DESC, id DESC.
          2. Inverte a lista para retornar em ordem cronológica.

    A ordenação dupla (created_at + id) é determinística: se duas mensagens
    tiverem
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
        "[chat_service] Histórico recuperado — session=%s | %s msgs",
        session_id,
        len(history),
    )
    return history


def build_openclaw_prompt(historico: list[dict[str, str]]) -> str:
    """Monta um prompt textual simples a partir do histórico da conversa."""
    linhas = [
        "Você é o Yumi Agent, assistente virtual de clínica veterinária.",
        "Use o histórico abaixo para responder a última mensagem do usuário.",
        "",
        "Histórico:",
    ]

    for item in historico:
        role = "Usuário" if item["role"] == "user" else "Assistente"
        linhas.append(f"{role}: {item['message']}")

    return "\n".join(linhas)


def generate_local_response(
    db: Session,
    clinica_id: str,
    mensagem: str,
    historico: list[dict[str, str]],
    agent_factory: AgentFactory = YumiAgent,
) -> dict[str, Any]:
    """Executa o fallback local via YumiAgent."""
    agent = agent_factory(clinica_id=clinica_id, db=db)
    return agent.handle_message(mensagem, historico=historico)


def normalize_stream_event_to_chunk(event: Any) -> str:
    """Normaliza evento de stream em chunk textual para HTTP."""
    if isinstance(event, str):
        return event

    if isinstance(event, dict):
        for key in ("payload", "text", "message", "content", "result"):
            value = event.get(key)
            if isinstance(value, str):
                return value
        return json.dumps(event, ensure_ascii=False)

    return str(event)


async def process_chat_stream(
    db: Session,
    clinica_id: str,
    usuario_id: str,
    mensagem: str,
    session_id: str | None = None,
    *,
    openclaw_client: OpenClawClient | None = None,
    agent_factory: AgentFactory = YumiAgent,
) -> AsyncGenerator[str, None]:
    """Orquestra o fluxo de chat em modo streaming com fallback."""
    record_stream_request()
    started_at = time.perf_counter()

    session = get_or_create_session(
        db=db,
        clinica_id=clinica_id,
        usuario_id=usuario_id,
        session_id=session_id,
        canal="chat",
    )
    session_identifier = str(session.id)

    save_message(
        db=db,
        session_id=session_identifier,
        role="user",
        message=mensagem,
    )
    historico = get_history(db=db, session_id=session_identifier, limit=20)

    chunks_sent: list[str] = []

    if settings.USE_OPENCLAW:
        client = openclaw_client or get_openclaw_client()
        prompt = build_openclaw_prompt(historico)

        try:
            async for event in client.stream_prompt(prompt):
                chunk = normalize_stream_event_to_chunk(event)
                chunks_sent.append(chunk)
                yield chunk

            record_openclaw_success()
            logger.info(
                "[chat_service] Stream concluído via OpenClaw | session=%s",
                session_identifier,
            )
        except (
            TimeoutError,
            ConnectionClosed,
            WebSocketException,
            OSError,
        ):
            record_openclaw_error()
            record_openclaw_fallback()
            logger.warning(
                "[chat_service] Falha no stream OpenClaw; fallback local "
                "| session=%s",
                session_identifier,
                exc_info=True,
            )
            fallback = generate_local_response(
                db=db,
                clinica_id=clinica_id,
                mensagem=mensagem,
                historico=historico,
                agent_factory=agent_factory,
            )
            fallback_chunk = fallback["resposta"]
            chunks_sent = [fallback_chunk]
            yield fallback_chunk
        except Exception:
            record_openclaw_error()
            record_openclaw_fallback()
            logger.error(
                "[chat_service] Erro inesperado no stream OpenClaw; "
                "fallback local | session=%s",
                session_identifier,
                exc_info=True,
            )
            fallback = generate_local_response(
                db=db,
                clinica_id=clinica_id,
                mensagem=mensagem,
                historico=historico,
                agent_factory=agent_factory,
            )
            fallback_chunk = fallback["resposta"]
            chunks_sent = [fallback_chunk]
            yield fallback_chunk
    else:
        logger.info(
            "[chat_service] OpenClaw desativado por configuração; "
            "stream local em chunk único | session=%s",
            session_identifier,
        )
        fallback = generate_local_response(
            db=db,
            clinica_id=clinica_id,
            mensagem=mensagem,
            historico=historico,
            agent_factory=agent_factory,
        )
        fallback_chunk = fallback["resposta"]
        chunks_sent = [fallback_chunk]
        yield fallback_chunk

    final_response = "".join(chunks_sent)
    record_response_size(len(final_response))
    record_stream_duration(time.perf_counter() - started_at)

    save_message(
        db=db,
        session_id=session_identifier,
        role="assistant",
        message=final_response,
    )


async def process_chat_message(
    db: Session,
    clinica_id: str,
    usuario_id: str,
    mensagem: str,
    session_id: str | None = None,
    *,
    openclaw_client: OpenClawClient | None = None,
    agent_factory: AgentFactory = YumiAgent,
) -> ChatResult:
    """Orquestra o fluxo de chat com OpenClaw e fallback local."""
    record_chat_request()
    started_at = time.perf_counter()

    session = get_or_create_session(
        db=db,
        clinica_id=clinica_id,
        usuario_id=usuario_id,
        session_id=session_id,
        canal="chat",
    )
    session_identifier: str = str(session.id)

    save_message(
        db=db,
        session_id=session_identifier,
        role="user",
        message=mensagem,
    )
    historico = get_history(db=db, session_id=session_identifier, limit=20)

    resultado: dict[str, Any]

    if settings.USE_OPENCLAW:
        client = openclaw_client or get_openclaw_client()
        prompt = build_openclaw_prompt(historico)

        try:
            resposta = await client.send_prompt(prompt)
            resultado = {
                "intencao": "openclaw",
                "resposta": resposta,
                "dados": None,
            }
            record_openclaw_success()
            logger.info(
                "[chat_service] Resposta gerada via OpenClaw | session=%s",
                session_identifier,
            )
        except (
            TimeoutError,
            ConnectionClosed,
            WebSocketException,
            OSError,
        ):
            record_openclaw_error()
            record_openclaw_fallback()
            logger.warning(
                "[chat_service] OpenClaw indisponível; usando fallback local "
                "| session=%s",
                session_identifier,
                exc_info=True,
            )
            resultado = generate_local_response(
                db=db,
                clinica_id=clinica_id,
                mensagem=mensagem,
                historico=historico,
                agent_factory=agent_factory,
            )
        except Exception:
            record_openclaw_error()
            record_openclaw_fallback()
            logger.error(
                "[chat_service] Erro inesperado no OpenClaw; usando fallback "
                "local | session=%s",
                session_identifier,
                exc_info=True,
            )
            resultado = generate_local_response(
                db=db,
                clinica_id=clinica_id,
                mensagem=mensagem,
                historico=historico,
                agent_factory=agent_factory,
            )
    else:
        logger.info(
            "[chat_service] OpenClaw desativado por configuração; usando "
            "YumiAgent local | session=%s",
            session_identifier,
        )
        resultado = generate_local_response(
            db=db,
            clinica_id=clinica_id,
            mensagem=mensagem,
            historico=historico,
            agent_factory=agent_factory,
        )

    final_response = resultado["resposta"]
    record_response_size(len(final_response))
    record_chat_latency(time.perf_counter() - started_at)

    save_message(
        db=db,
        session_id=session_identifier,
        role="assistant",
        message=final_response,
    )

    return {
        "intencao": resultado["intencao"],
        "resposta": resultado["resposta"],
        "dados": resultado.get("dados"),
        "session_id": session_identifier,
    }
