"""Testes unitários da instrumentação de métricas no chat_service."""

# pylint: disable=redefined-outer-name

from unittest.mock import MagicMock

import pytest

from yumi.core import metrics
from yumi.services import chat_service


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.id = "sessao-metrics-123"
    return session


class DummyOpenClawSuccess:
    """Cliente stub de sucesso para /chat."""

    async def send_prompt(self, _prompt):
        return "resposta openclaw"


class DummyOpenClawError:
    """Cliente stub com erro para /chat."""

    async def send_prompt(self, _prompt):
        raise TimeoutError()


class DummyOpenClawStreamSuccess:
    """Cliente stub de stream bem-sucedido."""

    async def stream_prompt(self, _prompt):
        yield "a"
        yield "b"


class DummyOpenClawStreamError:
    """Cliente stub de stream com erro."""

    async def stream_prompt(self, _prompt):
        raise RuntimeError("boom")


class TestChatMetrics:
    """Valida registro de métricas nos fluxos de chat."""

    @pytest.mark.asyncio
    async def test_process_chat_registra_metricas_sucesso_openclaw(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        metrics.reset_metrics()
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[{"role": "user", "message": "Oi"}]),
        )

        await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Oi",
            openclaw_client=DummyOpenClawSuccess(),
        )

        snapshot = metrics.get_metrics_snapshot()
        assert snapshot.chat_requests_total == 1
        assert snapshot.chat_openclaw_success_total == 1
        assert snapshot.chat_openclaw_fallback_total == 0
        assert snapshot.chat_openclaw_errors_total == 0
        assert len(snapshot.chat_response_time_seconds) == 1
        assert len(snapshot.chat_response_size_chars) == 1

    @pytest.mark.asyncio
    async def test_process_chat_registra_fallback_e_erro(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        metrics.reset_metrics()
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "fallback",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Oi",
            openclaw_client=DummyOpenClawError(),
            agent_factory=agent_factory,
        )

        snapshot = metrics.get_metrics_snapshot()
        assert snapshot.chat_requests_total == 1
        assert snapshot.chat_openclaw_success_total == 0
        assert snapshot.chat_openclaw_fallback_total == 1
        assert snapshot.chat_openclaw_errors_total == 1
        assert len(snapshot.chat_response_time_seconds) == 1
        assert len(snapshot.chat_response_size_chars) == 1

    @pytest.mark.asyncio
    async def test_process_chat_stream_registra_metricas_sucesso(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        metrics.reset_metrics()
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        chunks = []
        async for chunk in chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Oi",
            openclaw_client=DummyOpenClawStreamSuccess(),
        ):
            chunks.append(chunk)

        assert chunks == ["a", "b"]
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot.chat_stream_requests_total == 1
        assert snapshot.chat_openclaw_success_total == 1
        assert snapshot.chat_openclaw_fallback_total == 0
        assert snapshot.chat_openclaw_errors_total == 0
        assert len(snapshot.chat_stream_duration_seconds) == 1
        assert len(snapshot.chat_response_size_chars) == 1

    @pytest.mark.asyncio
    async def test_process_chat_stream_registra_fallback_e_erro(
        self,
        mock_db,
        mock_session,
        monkeypatch,
    ):
        metrics.reset_metrics()
        monkeypatch.setattr(chat_service.settings, "USE_OPENCLAW", True)
        monkeypatch.setattr(
            chat_service,
            "get_or_create_session",
            MagicMock(return_value=mock_session),
        )
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "fallback-stream",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        chunks = []
        async for chunk in chat_service.process_chat_stream(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Oi",
            openclaw_client=DummyOpenClawStreamError(),
            agent_factory=agent_factory,
        ):
            chunks.append(chunk)

        assert chunks == ["fallback-stream"]
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot.chat_stream_requests_total == 1
        assert snapshot.chat_openclaw_success_total == 0
        assert snapshot.chat_openclaw_fallback_total == 1
        assert snapshot.chat_openclaw_errors_total == 1
        assert len(snapshot.chat_stream_duration_seconds) == 1
        assert len(snapshot.chat_response_size_chars) == 1
