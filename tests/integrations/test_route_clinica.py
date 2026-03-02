from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import (
    get_current_admin,
    get_current_atendente,
    get_current_clinica_id,
    verificar_mesma_clinica,
)
from yumi.core.database import get_db
from yumi.main import app
from yumi.models.clinica import Clinica


@pytest.fixture
def client():
    """Cliente de teste da API."""
    return TestClient(app)


@pytest.fixture
def mock_usuario_admin():
    """Mock de usuário admin para testes."""
    usuario = Mock()
    usuario.id = "user-admin-123"
    usuario.nome = "Admin Teste"
    usuario.email = "admin@teste.com"
    usuario.role = "admin"
    usuario.clinica_id = "clinica-123"
    usuario.ativo = True
    usuario.ultimo_login = datetime.now()
    return usuario


@pytest.fixture
def mock_usuario_atendente():
    """Mock de usuário atendente para testes."""
    usuario = Mock()
    usuario.id = "user-atend-123"
    usuario.nome = "Atendente Teste"
    usuario.email = "atendente@teste.com"
    usuario.role = "atendente"
    usuario.clinica_id = "clinica-123"
    usuario.ativo = True
    usuario.ultimo_login = datetime.now()
    return usuario


@pytest.fixture
def mock_clinica():
    """Mock de clínica para testes."""
    clinica = Mock(spec=Clinica)
    clinica.id = "clinica-123"
    clinica.nome = "Clínica Teste"
    clinica.endereco = "Rua Teste, 123"
    clinica.ativo = True
    clinica.configuracoes = {}
    clinica.created_at = datetime.now()
    clinica.updated_at = datetime.now()
    return clinica


@pytest.fixture
def mock_db():
    """Mock da sessão do banco."""
    db = Mock()
    return db


class TestClinicaRoutes:
    """Testes para endpoints de clínicas."""
    
    def setup_method(self):
        """Limpa as sobrescritas de dependência antes de cada teste."""
        app.dependency_overrides.clear()
    
    def teardown_method(self):
        """Limpa as sobrescritas de dependência após cada teste."""
        app.dependency_overrides.clear()
    
    @patch('yumi.api.clinica_routes.clinica_service.create_clinica')
    def test_criar_clinica_sucesso(self, mock_create, client, mock_usuario_admin, mock_clinica, mock_db):
        """Testa POST /api/v1/clinicas com sucesso."""
        # Arrange
        app.dependency_overrides[get_current_admin] = lambda: mock_usuario_admin
        app.dependency_overrides[get_db] = lambda: mock_db
        mock_create.return_value = mock_clinica
        payload = {
            "nome": "Clínica Teste",
            "endereco": "Rua Teste, 123"
        }
        
        # Act
        response = client.post("/api/v1/clinicas", json=payload)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == "clinica-123"
    
    @patch('yumi.api.clinica_routes.clinica_service.create_clinica')
    def test_criar_clinica_dados_invalidos(self, mock_create, client, mock_usuario_admin, mock_db):
        """Testa criação com dados inválidos."""
        # Arrange
        app.dependency_overrides[get_current_admin] = lambda: mock_usuario_admin
        app.dependency_overrides[get_db] = lambda: mock_db
        payload = {
            "nome": "AB"  # Nome muito curto
        }
        
        # Act
        response = client.post("/api/v1/clinicas", json=payload)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    @patch('yumi.api.clinica_routes.clinica_service.listar_clinicas')
    def test_listar_clinicas_sucesso(self, mock_listar, client, mock_usuario_atendente, mock_clinica, mock_db):
        """Testa GET /api/v1/clinicas."""
        # Arrange
        app.dependency_overrides[get_current_atendente] = lambda: mock_usuario_atendente
        app.dependency_overrides[get_current_clinica_id] = lambda: mock_usuario_atendente.clinica_id
        app.dependency_overrides[get_db] = lambda: mock_db
        mock_listar.return_value = [mock_clinica]
        
        # Act
        response = client.get("/api/v1/clinicas")
        
        # Assert
        assert response.status_code == 200
        assert "clinicas" in response.json()
        assert len(response.json()["clinicas"]) == 1
    
    @patch('yumi.api.clinica_routes.clinica_service.get_clinica_by_id')
    def test_obter_clinica_por_id_sucesso(self, mock_get, client, mock_usuario_atendente, mock_clinica, mock_db):
        """Testa GET /api/v1/clinicas/{id}."""
        # Arrange
        app.dependency_overrides[get_current_atendente] = lambda: mock_usuario_atendente
        app.dependency_overrides[get_current_clinica_id] = lambda: mock_usuario_atendente.clinica_id
        app.dependency_overrides[verificar_mesma_clinica] = lambda: None
        app.dependency_overrides[get_db] = lambda: mock_db
        mock_get.return_value = mock_clinica
        
        # Act
        response = client.get("/api/v1/clinicas/clinica-123")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "clinica-123"
    
    @patch('yumi.api.clinica_routes.clinica_service.update_clinica')
    def test_atualizar_clinica_sucesso(self, mock_update, client, mock_usuario_admin, mock_clinica, mock_db):
        """Testa PUT /api/v1/clinicas/{id}."""
        # Arrange
        app.dependency_overrides[get_current_admin] = lambda: mock_usuario_admin
        app.dependency_overrides[get_current_clinica_id] = lambda: mock_usuario_admin.clinica_id
        app.dependency_overrides[verificar_mesma_clinica] = lambda: None
        app.dependency_overrides[get_db] = lambda: mock_db
        mock_update.return_value = mock_clinica
        payload = {
            "nome": "Clínica Atualizada"
        }
        
        # Act
        response = client.put("/api/v1/clinicas/clinica-123", json=payload)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == "clinica-123"
    
    @patch('yumi.api.clinica_routes.clinica_service.delete_clinica')
    def test_deletar_clinica_sucesso(self, mock_delete, client, mock_usuario_admin, mock_clinica, mock_db):
        """Testa DELETE /api/v1/clinicas/{id}."""
        # Arrange
        app.dependency_overrides[get_current_admin] = lambda: mock_usuario_admin
        app.dependency_overrides[get_current_clinica_id] = lambda: mock_usuario_admin.clinica_id
        app.dependency_overrides[verificar_mesma_clinica] = lambda: None
        app.dependency_overrides[get_db] = lambda: mock_db
        mock_clinica.ativo = False
        mock_delete.return_value = mock_clinica
        
        # Act
        response = client.delete("/api/v1/clinicas/clinica-123")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["clinica"]["ativo"] is False
