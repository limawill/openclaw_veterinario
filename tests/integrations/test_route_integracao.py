from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.main import app


@pytest.fixture
def client():
    """Cliente de teste da API."""
    return TestClient(app)


class TestIntegracaoRoutes:
    """Testes para endpoints de integrações."""
    
    @patch('yumi.api.integracao_routes.integracao_service.criar_integracao')
    def test_criar_integracao_google_calendar(self, mock_criar, client):
        """Testa POST /api/v1/integracoes - Google Calendar."""
        # Arrange
        mock_integracao = Mock()
        mock_integracao.id = "4287a1de-33d4-43c4-ada4-9e0776525531"
        mock_integracao.clinica_id = "385f65ba-cf4c-4405-bc1b-39fd7683b25f"
        mock_integracao.tipo_servico = "google_calendar"
        mock_integracao.credenciais = {"access_token": "token123"}
        mock_integracao.ativo = True
        mock_integracao.created_at = datetime.now()
        mock_integracao.updated_at = datetime.now()
        mock_integracao.nome_clinica = "Clínica Teste"
        mock_criar.return_value = mock_integracao
        
        payload = {
            "clinica_id": "385f65ba-cf4c-4405-bc1b-39fd7683b25f",
            "tipo_servico": "google_calendar",
            "credenciais": {
                "access_token": "token123",
                "refresh_token": "refresh123",
                "calendar_id": "primary"
            }
        }
        
        # Act
        response = client.post("/api/v1/integracoes", json=payload)
        
        # Assert
        assert response.status_code == 201
    
    @patch('yumi.api.integracao_routes.integracao_service.listar_integracoes')
    def test_listar_integracoes_com_filtros(self, mock_listar, client):
        """Testa GET /api/v1/integracoes com filtros."""
        # Arrange
        mock_listar.return_value = ([], 0)
        
        # Act
        response = client.get(
            "/api/v1/integracoes",
            params={
                "clinica_id": "385f65ba-cf4c-4405-bc1b-39fd7683b25f",
                "tipo_servico": "whatsapp"
            }
        )
        
        # Assert
        assert response.status_code == 200
    
    @patch('yumi.api.integracao_routes.integracao_service.testar_integracao')
    def test_testar_integracao_sucesso(self, mock_testar, client):
        """Testa POST /api/v1/integracoes/{id}/testar."""
        # Arrange
        mock_testar.return_value = {
            "sucesso": True,
            "mensagem": "Conexão estabelecida",
            "detalhes": {}
        }
        
        # Act
        response = client.post("/api/v1/integracoes/4287a1de-33d4-43c4-ada4-9e0776525531/testar")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["sucesso"] is True
    
    @patch('yumi.api.integracao_routes.integracao_service.ativar_integracao')
    def test_ativar_desativar_integracao(self, mock_ativar, client):
        """Testa PATCH /api/v1/integracoes/{id}/ativar."""
        # Arrange
        mock_integracao = Mock()
        mock_integracao.id = "4287a1de-33d4-43c4-ada4-9e0776525531"
        mock_integracao.clinica_id = "385f65ba-cf4c-4405-bc1b-39fd7683b25f"
        mock_integracao.tipo_servico = "google_calendar"
        mock_integracao.credenciais = {"access_token": "token123"}
        mock_integracao.ativo = False
        mock_integracao.created_at = datetime.now()
        mock_integracao.updated_at = datetime.now()
        mock_integracao.nome_clinica = "Clínica Teste"
        mock_ativar.return_value = mock_integracao
        
        # Act
        response = client.patch(
            "/api/v1/integracoes/4287a1de-33d4-43c4-ada4-9e0776525531/ativar",
            params={"ativo": False}
        )
        
        # Assert
        assert response.status_code == 200