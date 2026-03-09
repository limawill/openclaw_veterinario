"""
test_route_agent.py — Testes de integração para POST /api/v1/agent/chat.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import get_current_atendente
from yumi.core.database import get_db
from yumi.main import app

CLINICA_ID = "170a7399-4b47-4ad1-a10b-a8ac69b4a166"
OUTRA_CLINICA_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CHAT_URL = "/api/v1/agent/chat"


@pytest.fixture
def client():
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
        app.dependency_overrides[get_current_atendente] = lambda: self.mock_usuario

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
    # INTENÇÕES — mock do YumiAgent
    # =====================================================

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_listar_veterinarios(self, mock_agent_class, client):
        """Deve chamar o agente e retornar resposta para intenção de listar."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "listar_veterinarios",
            "resposta": "Temos 2 veterinários disponíveis.",
            "dados": {"total": 2, "veterinarios": []},
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Quais veterinários vocês têm?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "listar_veterinarios"
        assert "veterinários" in data["resposta"]
        assert data["dados"]["total"] == 2
        # Verifica que 'session_id' está presente no response
        assert "session_id" in data
        assert data["session_id"] is not None

        # Verifica que o agente foi instanciado com os parâmetros corretos
        mock_agent_class.assert_called_once_with(
            clinica_id=CLINICA_ID,
            db=self.mock_db
        )
        # Verifica que handle_message foi chamado com histórico (vazio para sessão nova)
        mock_agent.handle_message.assert_called_once_with(
            "Quais veterinários vocês têm?",
            historico=[]
        )

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_ver_agendamentos(self, mock_agent_class, client):
        """Deve retornar resposta para intenção de ver agendamentos."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "ver_agendamentos",
            "resposta": "Hoje temos 3 consultas agendadas.",
            "dados": {"total": 3, "agendamentos": []},
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Quais são os agendamentos de hoje?"
        })

        assert response.status_code == 200
        assert response.json()["intencao"] == "ver_agendamentos"

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_intencao_desconhecida(self, mock_agent_class, client):
        """Deve retornar 200 mesmo para intenção desconhecida."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Não entendi. Posso ajudar com agendamentos e veterinários.",
            "dados": None,
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "qual o endereço da clínica?"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["intencao"] == "desconhecido"
        assert data["dados"] is None

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_dados_pode_ser_none(self, mock_agent_class, client):
        """Deve retornar 200 quando agente retorna dados=None."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Não entendi sua solicitação.",
            "dados": None,
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "teste"
        })

        assert response.status_code == 200
        assert response.json()["dados"] is None

    # =====================================================
    # SESSÃO DE CONVERSA
    # =====================================================

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_response_contem_session_id(self, mock_agent_class, client):
        """Toda resposta deve conter session_id (nova sessão criada automaticamente)."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Olá!",
            "dados": None,
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Olá"
        })

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_sem_session_id_cria_nova_sessao(self, mock_agent_class, client):
        """Quando session_id não enviado, gera novo session_id na resposta."""
        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Olá!",
            "dados": None,
        }
        mock_agent_class.return_value = mock_agent

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

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_session_id_invalido_retorna_404(self, mock_agent_class, client):
        """Quando session_id enviado não existe no banco, deve retornar 404."""
        # Configura o mock para simular sessão não encontrada
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Mensagem contínua",
            "session_id": "session-que-nao-existe",
        })

        assert response.status_code == 404
        # O agente NÃO deve ser chamado quando a sessão não existe
        mock_agent.handle_message.assert_not_called()

    @patch("yumi.api.agent_routes.YumiAgent")
    def test_chat_com_session_id_valido_reutiliza_sessao(self, mock_agent_class, client):
        """Quando session_id válido enviado, deve retornar o mesmo session_id."""
        existing_session_id = "sessao-existente-uuid-1234567890a"

        mock_session = MagicMock()
        mock_session.id = existing_session_id

        # Configura first() para retornar a sessão existente
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        # Configura all() para retornar histórico vazio
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        mock_agent = MagicMock()
        mock_agent.handle_message.return_value = {
            "intencao": "desconhecido",
            "resposta": "Continuando nossa conversa!",
            "dados": None,
        }
        mock_agent_class.return_value = mock_agent

        response = client.post(CHAT_URL, json={
            "clinica_id": CLINICA_ID,
            "mensagem": "Continuando...",
            "session_id": existing_session_id,
        })

        assert response.status_code == 200
        assert response.json()["session_id"] == existing_session_id
