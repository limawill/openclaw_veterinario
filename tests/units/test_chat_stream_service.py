"""Testes unitários do serviço de streaming de chat."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from yumi.services import chat_service


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.id = "sessao-stream-123"
    return session


class DummyOpenClawClient:
    """Stub simples para stream de eventos do OpenClaw."""

    def __init__(self, events):
        self._events = events

    async def stream_prompt(self, _prompt):
        for event in self._events:
            yield event


class TimeoutOpenClawClient:
    """Stub que simula timeout durante iteração do stream."""

    async def stream_prompt(self, _prompt):
        raise TimeoutError()
        yield "unused"


class ErrorOpenClawClient:
    """Stub que simula erro inesperado no stream."""

    async def stream_prompt(self, _prompt):
        raise RuntimeError("boom")
        yield "unused"


class TestChatStreamService:
    """Valida comportamento de streaming e fallback no service."""

    @pytest.mark.asyncio
    async def test_streaming_via_openclaw_multiples_chunks(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        save_message_mock = MagicMock()
        monkeypatch.setattr(chat_service, "save_message", save_message_mock)
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[{"role": "user", "message": "Olá"}]),
        )

        client = DummyOpenClawClient(
            [
                "chunk 1",
                {"payload": "chunk 2"},
                {"foo": "bar"},
            ]
        )

        chunks = []
        async for chunk in chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=client,
        ):
            chunks.append(chunk)

        assert chunks[0] == "chunk 1"
        assert chunks[1] == "chunk 2"
        assert chunks[2] == '{"foo": "bar"}'
        assert save_message_mock.call_count == 2
        assert save_message_mock.call_args_list[1].kwargs["message"] == (
            "chunk 1chunk 2{\"foo\": \"bar\"}"
        )

    @pytest.mark.asyncio
    async def test_fallback_streaming_via_yumiagent_quando_flag_desativada(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", False)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        save_message_mock = MagicMock()
        monkeypatch.setattr(chat_service, "save_message", save_message_mock)
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "fallback unico",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)
        openclaw_client = MagicMock()
        openclaw_client.stream_prompt = AsyncMock()

        chunks = []
        async for chunk in chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=openclaw_client,
            agent_factory=agent_factory,
        ):
            chunks.append(chunk)

        assert chunks == ["fallback unico"]
        openclaw_client.stream_prompt.assert_not_called()
        assert save_message_mock.call_args_list[1].kwargs["message"] == (
            "fallback unico"
        )

    @pytest.mark.asyncio
    async def test_fallback_em_timeout_durante_stream(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        save_message_mock = MagicMock()
        monkeypatch.setattr(chat_service, "save_message", save_message_mock)
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "resposta fallback",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        chunks = []
        async for chunk in chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=TimeoutOpenClawClient(),
            agent_factory=agent_factory,
        ):
            chunks.append(chunk)

        assert chunks == ["resposta fallback"]
        assert save_message_mock.call_args_list[1].kwargs["message"] == (
            "resposta fallback"
        )

    @pytest.mark.asyncio
    async def test_finalizacao_correta_do_generator_em_erro_inesperado(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        save_message_mock = MagicMock()
        monkeypatch.setattr(chat_service, "save_message", save_message_mock)
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "fallback erro",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        generator = chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=ErrorOpenClawClient(),
            agent_factory=agent_factory,
        )

        chunks = []
        async for chunk in generator:
            chunks.append(chunk)

        assert chunks == ["fallback erro"]
        assert save_message_mock.call_count == 2
        assert save_message_mock.call_args_list[1].kwargs["message"] == (
            "fallback erro"
        )
