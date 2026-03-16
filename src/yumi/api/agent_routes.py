"""
agent_routes.py — Rota de entrada para o Yumi Agent.

Responsabilidade:
    Orquestrar a chamada ao YumiAgent — sem lógica de negócio aqui.
    A rota é apenas um "porteiro":
      1. Valida autenticação
      2. Valida isolamento multi-tenant
      3. Instancia o agente
      4. Retorna a resposta

Canais futuros que usarão este endpoint:
    - WhatsApp
    - Telegram
    - Chat no site da clínica
    - App mobile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from yumi.agents.yumi_agent.yumi import YumiAgent
from yumi.auth.dependencies import Usuario, get_current_atendente
from yumi.core.database import get_db
from yumi.core.logger import logger
from yumi.schemas.schemas_chat import ChatRequest, ChatResponse
from yumi.services.chat_service import process_chat_message, process_chat_stream

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar mensagem ao Yumi Agent",
    description="""
    Ponto de entrada único para todos os canais de comunicação
    com o Yumi Agent.

    O agente detecta a intenção da mensagem e executa a ação correspondente.

    **Intenções suportadas (Fase 1 — MVP):**
    - `listar_veterinarios` — "quais veterinários vocês têm?"
    - `ver_agendamentos` — "quais consultas têm hoje?"
    - `ver_horarios` — "quais horários estão disponíveis?"
    - `agendar_consulta` — "quero marcar uma consulta"
    - `desconhecido` — mensagem não reconhecida

    **Segurança:**
    - Requer autenticação via Bearer Token (JWT)
    - O `clinica_id` do body deve corresponder ao `clinica_id` do token
    """,
    responses={
        200: {"description": "Agente respondeu com sucesso"},
        401: {"description": "Token JWT ausente ou inválido"},
        403: {
            "description": (
                "Acesso negado — clinica_id não corresponde ao token"
            )
        },
        422: {"description": "Mensagem ausente ou inválida"},
    },
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_atendente),
):
    """
    Recebe uma mensagem e retorna a resposta do Yumi Agent.

    Proteção multi-tenant:
        O clinica_id enviado no body é validado contra o clinica_id
        presente no token JWT do usuário autenticado.
        Isso impede que um usuário de uma clínica acesse dados de outra.
    """
    # Validação multi-tenant equivalente ao verificar_mesma_clinica.
    # mas feita inline pois clinica_id vem do body (não da URL)
    if current_user.clinica_id != request.clinica_id:
        logger.warning(
            "[/chat] Tentativa de acesso cruzado: usuário %s "
            "(clínica %s) tentou acessar clínica %s",
            current_user.email,
            current_user.clinica_id,
            request.clinica_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado — clinica_id não corresponde ao seu token",
        )

    logger.info(
        "[/chat] Mensagem de %s (clínica %s): '%s'",
        current_user.email,
        request.clinica_id,
        request.mensagem,
    )

    resultado = await process_chat_message(
        db=db,
        clinica_id=request.clinica_id,
        usuario_id=str(current_user.id),
        mensagem=request.mensagem,
        session_id=request.session_id,
        agent_factory=YumiAgent,
    )

    logger.info(
        "[/chat] Resposta gerada — intenção: %s | sessão: %s",
        resultado["intencao"],
        resultado["session_id"],
    )

    return ChatResponse(
        intencao=resultado["intencao"],
        resposta=resultado["resposta"],
        dados=resultado.get("dados"),
        session_id=resultado["session_id"],
    )


@router.post(
    "/chat/stream",
    status_code=status.HTTP_200_OK,
    summary="Enviar mensagem ao Yumi Agent (streaming)",
    description="""
    Endpoint de streaming para respostas em chunks.

    Fluxo:
    - persiste mensagem e histórico
    - tenta stream via OpenClaw quando habilitado
    - aplica fallback local em falhas
    """,
    responses={
        200: {"description": "Stream iniciado com sucesso"},
        401: {"description": "Token JWT ausente ou inválido"},
        403: {
            "description": (
                "Acesso negado — clinica_id não corresponde ao token"
            )
        },
        422: {"description": "Mensagem ausente ou inválida"},
    },
)
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_atendente),
):
    """Recebe mensagem e retorna stream textual da resposta do agente."""
    if current_user.clinica_id != request.clinica_id:
        logger.warning(
            "[/chat/stream] Tentativa de acesso cruzado: usuário %s "
            "(clínica %s) tentou acessar clínica %s",
            current_user.email,
            current_user.clinica_id,
            request.clinica_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado — clinica_id não corresponde ao seu token",
        )

    logger.info(
        "[/chat/stream] Mensagem de %s (clínica %s): '%s'",
        current_user.email,
        request.clinica_id,
        request.mensagem,
    )

    stream = process_chat_stream(
        db=db,
        clinica_id=request.clinica_id,
        usuario_id=str(current_user.id),
        mensagem=request.mensagem,
        session_id=request.session_id,
        agent_factory=YumiAgent,
    )

    return StreamingResponse(stream, media_type="text/plain")
