"""test_route_agent.py — Testes de integração para POST /api/v1/agent/chat."""

# pylint: disable=attribute-defined-outside-init,redefined-outer-name

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import get_current_atendente
from yumi.core.database import get_db
from yumi.main import app

CLINICA_ID = "170a7399-4b47-4ad1-a10b-a8ac69b4a166"
OUTRA_CLINICA_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CHAT_URL = "/api/v1/agent/chat"


@pytest.fixture(name="client")
def _client():
    return TestClient(app)


class TestChatRoute:
    """Testes para o endpoint POST /api/v1/agent/chat."""

    def setup_method(self):
        """Configura mocks de autenticação e banco antes de cada teste."""
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

    # =====================================================
    # AUTENTICAÇÃO
    # =====================================================

    def test_chat_sem_autenticacao(self, client):
        """Deve retornar 401 quando token não fornecido."""
        app.dependency_overrides.clear()  # Remove o override do setup

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Olá"
        })

        assert response.status_code == 401

    # =====================================================
    # VALIDAÇÃO MULTI-TENANT
    # =====================================================

    def test_chat_clinica_errada_retorna_403(self, client):
        """Deve retornar 403 quando clinica_id do body difere do token."""
        response = client.post(CHAT_URL, json={
            "clinica_id": OUTRA_CLINICA_ID,  # diferente do token
            "mensagem": "Quais veterinários vocês têm?"
        })

        assert response.status_code == 403
        assert "clinica_id" in response.json()["detail"].lower()

    # =====================================================
    # VALIDAÇÃO DE SCHEMA
    # =====================================================

    def test_chat_mensagem_vazia_retorna_422(self, client):
        """Deve retornar 422 quando mensagem está vazia."""
        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": ""
        })

        assert response.status_code == 422

    def test_chat_sem_clinica_id_retorna_422(self, client):
        """Deve retornar 422 quando clinica_id está ausente."""
        response = client.post(CHAT_URL, json={
            "mensagem": "Olá"
        })

        assert response.status_code == 422

    def test_chat_sem_mensagem_retorna_422(self, client):
        """Deve retornar 422 quando mensagem está ausente."""
        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
        })

        assert response.status_code == 422

    # =====================================================
    # FLUXO DA ROTA — delegação ao serviço
    # =====================================================

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_listar_veterinarios(self, mock_process_chat, client):
        """Deve delegar ao serviço e retornar resposta de listar."""
        mock_process_chat.return_value = {
            "intencao": "listar_veterinarios",
            "resposta": "Temos 2 veterinários disponíveis.",
            "dados": {"total": 2, "veterinarios": []},
            "session_id": "sessao-123",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Quais veterinários vocês têm?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "listar_veterinarios"
        assert "veterinários" in data["resposta"]
        assert data["dados"]["total"] == 2
        assert data["session_id"] == "sessao-123"
        mock_process_chat.assert_awaited_once()
        called_kwargs = mock_process_chat.await_args.kwargs
        assert called_kwargs["db"] == self.mock_db
        assert called_kwargs["clinica_id"] == CLINICA_ID
        assert called_kwargs["usuario_id"] == self.mock_usuario.id
        assert called_kwargs["mensagem"] == "Quais veterinários vocês têm?"
        assert called_kwargs["session_id"] is None
        assert called_kwargs["agent_factory"].__name__ == "YumiAgent"

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_ver_agendamentos(self, mock_process_chat, client):
        """Deve retornar resposta para intenção de ver agendamentos."""
        mock_process_chat.return_value = {
            "intencao": "ver_agendamentos",
            "resposta": "Hoje temos 3 consultas agendadas.",
            "dados": {"total": 3, "agendamentos": []},
            "session_id": "sessao-123",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Quais são os agendamentos de hoje?"
        })

        assert response.status_code == 200
        assert response.json()["intencao"] == "ver_agendamentos"

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_intencao_desconhecida(self, mock_process_chat, client):
        """Deve retornar 200 mesmo para intenção desconhecida."""
        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": (
                "Não entendi. Posso ajudar com agendamentos e veterinários."
            ),
            "dados": None,
            "session_id": "sessao-123",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "qual o endereço da clínica?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "desconhecido"
        assert data["dados"] is None

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_dados_pode_ser_none(self, mock_process_chat, client):
        """Deve retornar 200 quando agente retorna dados=None."""
        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": "Não entendi sua solicitação.",
            "dados": None,
            "session_id": "sessao-123",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "teste"
        })

        assert response.status_code == 200
        assert response.json()["dados"] is None

    # =====================================================
    # SESSÃO DE CONVERSA
    # =====================================================

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_response_contem_session_id(self, mock_process_chat, client):
        """Toda resposta deve conter session_id na resposta da rota."""
        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": "Olá!",
            "dados": None,
            "session_id": "sessao-gerada",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Olá"
        })

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "sessao-gerada"

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_sem_session_id_cria_nova_sessao(
        self,
        mock_process_chat,
        client,
    ):
        """Quando session_id não enviado, gera novo session_id na resposta."""
        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": "Olá!",
            "dados": None,
            "session_id": "12345678-1234-1234-1234-123456789012",
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Primeira mensagem",
            # sem session_id
        })

        assert response.status_code == 200
        session_id = response.json()["session_id"]
        # Deve ser um UUID válido (string não vazia)
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # formato UUID

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_session_id_invalido_retorna_404(
        self,
        mock_process_chat,
        client,
    ):
        """Quando session_id enviado não existe no banco, deve retornar 404."""
        from fastapi import HTTPException

        mock_process_chat.side_effect = HTTPException(
            status_code=404,
            detail=(
                "Sessão 'session-que-nao-existe' não encontrada para esta "
                "clínica."
            ),
        )

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Mensagem contínua",
            "session_id": "session-que-nao-existe",
        })

        assert response.status_code == 404
        mock_process_chat.assert_awaited_once()

    @patch(
        "yumi.api.agent_routes.process_chat_message",
        new_callable=AsyncMock,
    )
    def test_chat_com_session_id_valido_reutiliza_sessao(
        self,
        mock_process_chat,
        client,
    ):
        """Quando session_id válido é enviado, a rota o preserva."""
        existing_session_id = "sessao-existente-uuid-1234567890a"

        mock_process_chat.return_value = {
            "intencao": "desconhecido",
            "resposta": "Continuando nossa conversa!",
            "dados": None,
            "session_id": existing_session_id,
        }

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Continuando...",
            "session_id": existing_session_id,
        })

        assert response.status_code == 200
        assert response.json()["session_id"] == existing_session_id
