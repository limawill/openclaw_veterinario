from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.main import app
from yumi.models.clinica import Clinica


@pytest.fixture
def client():
    """Cliente de teste da API."""
    return TestClient(app)


@pytest.fixture
def mock_clinica():
    """Mock de clínica para testes."""
    clinica = Mock(spec=Clinica)
    clinica.id = "clinica-123"
    clinica.nome = "Clínica Teste"
    clinica.endereco = "Rua Teste, 123"
    clinica.ativo = True
    clinica.configuracoes = {}
    clinica.created_at = None
    clinica.updated_at = None
    return clinica


class TestClinicaRoutes:
    """Testes para endpoints de clínicas."""
    
    @patch('yumi.api.clinica_routes.clinica_service.create_clinica')
    def test_criar_clinica_sucesso(self, mock_create, client, mock_clinica):
        """Testa POST /api/v1/clinicas com sucesso."""
        # Arrange
        mock_create.return_value = mock_clinica
        payload = {
            "nome": "Clínica Teste",
            "endereco": "Rua Teste, 123"
        }
        
        # Act
        response = client.post("/api/v1/clinicas", json=payload)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["mensagem"] == "Clínica criada com sucesso"
        assert response.json()["clinica"]["id"] == "clinica-123"
    
    @patch('yumi.api.clinica_routes.clinica_service.create_clinica')
    def test_criar_clinica_dados_invalidos(self, mock_create, client):
        """Testa criação com dados inválidos."""
        # Arrange
        payload = {
            "nome": "AB"  # Nome muito curto
        }
        
        # Act
        response = client.post("/api/v1/clinicas", json=payload)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('yumi.api.clinica_routes.clinica_service.listar_clinicas')
    def test_listar_clinicas_sucesso(self, mock_listar, client, mock_clinica):
        """Testa GET /api/v1/clinicas."""
        # Arrange
        mock_listar.return_value = [mock_clinica]
        
        # Act
        response = client.get("/api/v1/clinicas")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()["clinicas"]) == 1
    
    @patch('yumi.api.clinica_routes.clinica_service.get_clinica_by_id')
    def test_obter_clinica_por_id_sucesso(self, mock_get, client, mock_clinica):
        """Testa GET /api/v1/clinicas/{id}."""
        # Arrange
        mock_get.return_value = mock_clinica
        
        # Act
        response = client.get("/api/v1/clinicas/clinica-123")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["clinica"]["id"] == "clinica-123"
    
    @patch('yumi.api.clinica_routes.clinica_service.update_clinica')
    def test_atualizar_clinica_sucesso(self, mock_update, client, mock_clinica):
        """Testa PUT /api/v1/clinicas/{id}."""
        # Arrange
        mock_update.return_value = mock_clinica
        payload = {
            "nome": "Clínica Atualizada"
        }
        
        # Act
        response = client.put("/api/v1/clinicas/clinica-123", json=payload)
        
        # Assert
        assert response.status_code == 200
        assert "atualizada" in response.json()["mensagem"].lower()
    
    @patch('yumi.api.clinica_routes.clinica_service.delete_clinica')
    def test_deletar_clinica_sucesso(self, mock_delete, client, mock_clinica):
        """Testa DELETE /api/v1/clinicas/{id}."""
        # Arrange
        mock_clinica.ativo = False
        mock_delete.return_value = mock_clinica
        
        # Act
        response = client.delete("/api/v1/clinicas/clinica-123")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["clinica"]["ativo"] is False
