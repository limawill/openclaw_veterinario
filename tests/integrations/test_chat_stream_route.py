"""Testes de integração da rota /chat/stream."""

# pylint: disable=attribute-defined-outside-init,redefined-outer-name

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import get_current_atendente
from yumi.core.database import get_db
from yumi.main import app

CLINICA_ID = "170a7399-4b47-4ad1-a10b-a8ac69b4a166"
CHAT_STREAM_URL = "/api/v1/agent/chat/stream"


@pytest.fixture(name="client")
def _client():
    return TestClient(app)


async def gen_chunks(*chunks: str):
    for chunk in chunks:
        yield chunk


class TestChatStreamRoute:
    """Valida comportamento HTTP da rota de stream."""

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
        "yumi.api.agent_routes.process_chat_stream",
        new_callable=MagicMock,
    )
    def test_chat_stream_retorna_multiplos_chunks(
        self,
        mock_process_stream,
        client,
    ):
        mock_process_stream.return_value = gen_chunks(
            "chunk 1 ",
            "chunk 2 ",
            "chunk 3",
        )

        with client.stream(
            "POST",
            CHAT_STREAM_URL,
            json={"clinica_id": CLINICA_ID, "mensagem": "Olá"},
        ) as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert body == "chunk 1 chunk 2 chunk 3"
        assert response.headers["content-type"].startswith("text/plain")

    @patch(
        "yumi.api.agent_routes.process_chat_stream",
        new_callable=MagicMock,
    )
    def test_chat_stream_retorna_chunk_unico_no_fallback(
        self,
        mock_process_stream,
        client,
    ):
        mock_process_stream.return_value = gen_chunks("fallback local")

        with client.stream(
            "POST",
            CHAT_STREAM_URL,
            json={"clinica_id": CLINICA_ID, "mensagem": "Olá"},
        ) as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert body == "fallback local"

    @patch(
        "yumi.api.agent_routes.process_chat_stream",
        new_callable=MagicMock,
    )
    def test_chat_stream_serializacao_texto_simples(
        self,
        mock_process_stream,
        client,
    ):
        mock_process_stream.return_value = gen_chunks("abc", "def")

        with client.stream(
            "POST",
            CHAT_STREAM_URL,
            json={"clinica_id": CLINICA_ID, "mensagem": "Olá"},
        ) as response:
            chunks = list(response.iter_text())

        assert response.status_code == 200
        assert "".join(chunks) == "abcdef"
