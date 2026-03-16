"""Testes unitários da integração chat -> OpenClaw com fallback local."""

# pylint: disable=missing-module-docstring

from unittest.mock import AsyncMock, MagicMock

import pytest

from yumi.services import chat_service


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.id = "sessao-openclaw-123"
    return session


class TestChatOpenClawIntegration:
    """Valida a orquestração de chat no service."""

    @pytest.mark.asyncio
    async def test_chamada_bem_sucedida_via_openclaw(
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
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[{"role": "user", "message": "Olá"}]),
        )

        openclaw_client = MagicMock()
        openclaw_client.send_prompt = AsyncMock(
            return_value="Resposta do OpenClaw"
        )

        agent_factory = MagicMock()

        result = await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=openclaw_client,
            agent_factory=agent_factory,
        )

        assert result["intencao"] == "openclaw"
        assert result["resposta"] == "Resposta do OpenClaw"
        assert result["session_id"] == mock_session.id
        agent_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_para_yumiagent_quando_timeout(
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
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[{"role": "user", "message": "Olá"}]),
        )

        openclaw_client = MagicMock()
        openclaw_client.send_prompt = AsyncMock(side_effect=TimeoutError())

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Fallback local",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        result = await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=openclaw_client,
            agent_factory=agent_factory,
        )

        assert result["intencao"] == "desconhecido"
        assert result["resposta"] == "Fallback local"
        agent_factory.assert_called_once_with(
            clinica_id="clinica-1",
            db=mock_db,
        )
        mock_agent.handle_message.assert_called_once_with(
            "Olá",
            historico=[{"role": "user", "message": "Olá"}],
        )

    @pytest.mark.asyncio
    async def test_fallback_para_yumiagent_quando_excecao_generica(
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
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[{"role": "user", "message": "Olá"}]),
        )

        openclaw_client = MagicMock()
        openclaw_client.send_prompt = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "listar_veterinarios",
            "resposta": "Resposta local",
            "dados": {"total": 1},
        }
        agent_factory = MagicMock(return_value=mock_agent)

        result = await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=openclaw_client,
            agent_factory=agent_factory,
        )

        assert result["intencao"] == "listar_veterinarios"
        assert result["dados"] == {"total": 1}

    @pytest.mark.asyncio
    async def test_quando_flag_desativada_usa_direto_yumiagent(
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
        monkeypatch.setattr(chat_service, "save_message", MagicMock())
        monkeypatch.setattr(
            chat_service,
            "get_history",
            MagicMock(return_value=[]),
        )

        openclaw_client = MagicMock()
        openclaw_client.send_prompt = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Resposta local direta",
            "dados": None,
        }
        agent_factory = MagicMock(return_value=mock_agent)

        result = await chat_service.process_chat_message(
            db=mock_db,
            clinica_id="clinica-1",
            usuario_id="user-1",
            mensagem="Olá",
            openclaw_client=openclaw_client,
            agent_factory=agent_factory,
        )

        assert result["resposta"] == "Resposta local direta"
        openclaw_client.send_prompt.assert_not_called()
