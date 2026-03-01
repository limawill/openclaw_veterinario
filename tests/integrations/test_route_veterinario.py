from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.main import app
from yumi.models.veterinario import Veterinario


@pytest.fixture
def client():
    """Cliente de teste da API."""
    return TestClient(app)


@pytest.fixture
def mock_veterinario():
    """Mock de veterinário para testes."""
    vet = Mock(spec=Veterinario)
    vet.id = "4287a1de-33d4-43c4-ada4-9e0776525531"
    vet.nome = "Dr. João Silva"
    vet.email = "joao@email.com"
    vet.especialidade = "Clínica Geral"
    vet.ativo = True
    vet.created_at = None
    return vet


class TestVeterinarioRoutes:
    """Testes para endpoints de veterinários."""
    
    @patch('yumi.api.veterinario_routes.veterinario_service.create_veterinario')
    def test_criar_veterinario_sucesso(self, mock_create, client, mock_veterinario):
        """Testa POST /api/v1/veterinarios."""
        # Arrange
        mock_create.return_value = mock_veterinario
        payload = {
            "clinica_id": "751f3cba-fe70-4da3-b8ab-f7029196b352",
            "nome": "Dr. João Silva",
            "email": "joao@email.com",
            "especialidade": "Clínica Geral"
        }
        
        # Act
        response = client.post("/api/v1/veterinarios/", json=payload)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["veterinario"]["nome"] == "Dr. João Silva"
    
    @patch('yumi.api.veterinario_routes.veterinario_service.get_veterinario_by_id')
    def test_obter_veterinario_sucesso(self, mock_get, client, mock_veterinario):
        """Testa GET /api/v1/veterinarios/{id}."""
        # Arrange
        mock_get.return_value = mock_veterinario
        
        # Act
        response = client.get("/api/v1/veterinarios/4287a1de-33d4-43c4-ada4-9e0776525531")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["veterinario"]["id"] == "4287a1de-33d4-43c4-ada4-9e0776525531"
    
    @patch('yumi.api.veterinario_routes.veterinario_service.get_veterinarios_by_clinica')
    def test_listar_veterinarios_por_clinica(self, mock_listar, client, mock_veterinario):
        """Testa GET /api/v1/veterinarios/clinica/{id}."""
        # Arrange
        mock_listar.return_value = [mock_veterinario]
        
        # Act
        response = client.get("/api/v1/veterinarios/clinica/751f3cba-fe70-4da3-b8ab-f7029196b352")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()["veterinarios"]) == 1
    
    @patch('yumi.api.veterinario_routes.veterinario_service.delete_veterinario')
    def test_excluir_veterinario_sucesso(self, mock_delete, client, mock_veterinario):
        """Testa DELETE /api/v1/veterinarios/{id}."""
        # Arrange
        mock_veterinario.ativo = False
        mock_delete.return_value = mock_veterinario
        
        # Act
        response = client.delete("/api/v1/veterinarios/4287a1de-33d4-43c4-ada4-9e0776525531")
        
        # Assert
        assert response.status_code == 200
        assert "desativado" in response.json()["mensagem"].lower()
