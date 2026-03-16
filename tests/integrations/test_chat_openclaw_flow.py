"""Testes de integração do fluxo /chat com OpenClaw e fallback."""

# pylint: disable=attribute-defined-outside-init

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import get_current_atendente
from yumi.core.database import get_db
from yumi.main import app

CLINICA_ID = "170a7399-4b47-4ad1-a10b-a8ac69b4a166"
CHAT_URL = "/api/v1/agent/chat"


@pytest.fixture(name="client")
def _client():
    return TestClient(app)


class TestChatOpenClawFlow:
    """Valida a rota /chat com OpenClaw habilitado e fallback."""

    def setup_method(self):
        self.mock_db = MagicMock()

        self.mock_usuario = MagicMock()
        self.mock_usuario.id = "user-atend-123"
        self.mock_usuario.email = "atendente@openclaw.com"
        self.mock_usuario.role = "atendente"
        self.mock_usuario.clinica_id = CLINICA_ID
        self.mock_usuario.ativo = True

        app.dependency_overrides[get_db] = lambda: self.mock_db
        app.dependency_overrides[get_current_atendente] = (
            lambda: self.mock_usuario
        )

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_fluxo_chat_retorna_resposta_via_openclaw(
        self,
        mock_process_chat,
        client,
    ):
        mock_process_chat.return_value = {
            "intencao": "openclaw",
            "resposta": "Resposta do OpenClaw",
            "dados": None,
            "session_id": "sessao-openclaw",
        }

        response = client.post(
            CHAT_URL,
            json={"clinica_id": CLINICA_ID, "mensagem": "Olá"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "openclaw"
        assert data["resposta"] == "Resposta do OpenClaw"
        assert data["session_id"] == "sessao-openclaw"

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_fluxo_chat_retorna_resposta_fallback_local(
        self,
        mock_process_chat,
        client,
    ):
        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": "Fallback local ativo",
            "dados": None,
            "session_id": "sessao-fallback",
        }

        response = client.post(
            CHAT_URL,
            json={"clinica_id": CLINICA_ID, "mensagem": "Olá"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "desconhecido"
        assert data["resposta"] == "Fallback local ativo"
        assert data["session_id"] == "sessao-fallback"
