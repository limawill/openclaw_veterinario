# tests/integrations/test_auth_routes.py

"""
Testes de integração para as rotas de autenticação.
Testa o endpoint /auth/login e comportamentos relacionados.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.auth.dependencies import get_current_user
from yumi.core.database import get_db
from yumi.main import app


class TestAuthRoutes:
    """Testes para rotas de autenticação."""

    def setup_method(self):
        """Configura cliente de teste e mocks básicos."""
        self.client = TestClient(app)
        
        # Mock da sessão do banco
        self.mock_db = Mock()
        
        # Mock do usuário autenticado
        self.mock_usuario = Mock()
        self.mock_usuario.id = "c320813a-abcc-458a-ad4a-8bd08aa27ec2"
        self.mock_usuario.nome = "Usuário Teste"
        self.mock_usuario.email = "teste@email.com"
        self.mock_usuario.role = "admin"
        self.mock_usuario.clinica_id = "554800c9-b74c-453d-885f-5482d30e9acd"
        self.mock_usuario.ativo = True
        self.mock_usuario.ultimo_login = datetime.now()

        # Sobrescreve a dependência get_db
        app.dependency_overrides[get_db] = lambda: self.mock_db

    def teardown_method(self):
        """Limpa as sobrescritas de dependência."""
        app.dependency_overrides.clear()

    # =====================================================
    # TESTES DO ENDPOINT /auth/login
    # =====================================================

    @patch('yumi.auth.auth_routes.autenticar_usuario')
    def test_login_sucesso(self, mock_autenticar):
        """Deve retornar 200 e token quando credenciais corretas."""
        # Arrange
        mock_autenticar.return_value = "token.jwt.valido"
        
        login_data = {
            "username": "teste@email.com",
            "password": "senha123"
        }
        
        # Act
        response = self.client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["access_token"] == "token.jwt.valido"
        assert response.json()["token_type"] == "bearer"
        
        # Verifica se o serviço foi chamado corretamente
        mock_autenticar.assert_called_once_with(
            db=self.mock_db,
            email="teste@email.com",
            senha="senha123"
        )

    @patch('yumi.auth.auth_routes.autenticar_usuario')
    def test_login_credenciais_invalidas(self, mock_autenticar):
        """Deve retornar 401 quando credenciais inválidas."""
        # Arrange
        from fastapi import HTTPException
        mock_autenticar.side_effect = HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )
        
        login_data = {
            "username": "teste@email.com",
            "password": "senha_errada"
        }
        
        # Act
        response = self.client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 401
        assert response.json()["detail"] == "Credenciais inválidas"

    @patch('yumi.auth.auth_routes.autenticar_usuario')
    def test_login_usuario_inativo(self, mock_autenticar):
        """Deve retornar 403 quando usuário está inativo."""
        # Arrange
        from fastapi import HTTPException
        mock_autenticar.side_effect = HTTPException(
            status_code=403,
            detail="Usuário inativo. Contate o administrador."
        )
        
        login_data = {
            "username": "inativo@email.com",
            "password": "senha123"
        }
        
        # Act
        response = self.client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 403
        assert "Usuário inativo" in response.json()["detail"]

    def test_login_campo_faltando(self):
        """Deve retornar 422 quando campo obrigatório faltando."""
        # Arrange
        login_data = {
            "username": "teste@email.com"
            # password faltando
        }
        
        # Act
        response = self.client.post("/api/v1/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity

    # =====================================================
    # TESTES DO ENDPOINT /auth/logout
    # =====================================================

    def test_logout(self):
        """Endpoint logout deve retornar mensagem informativa."""
        # Act
        response = self.client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 200
        assert "mensagem" in response.json()
        assert "Logout realizado" in response.json()["mensagem"]

    # =====================================================
    # TESTES DO ENDPOINT /auth/me
    # =====================================================

    def test_get_current_user_info_sucesso(self):
        """Deve retornar dados do usuário com token válido."""
        # Arrange
        app.dependency_overrides[get_current_user] = lambda: self.mock_usuario
        
        # Act
        response = self.client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "c320813a-abcc-458a-ad4a-8bd08aa27ec2"
        assert data["nome"] == "Usuário Teste"
        assert data["email"] == "teste@email.com"
        assert data["role"] == "admin"
        assert data["clinica_id"] == "554800c9-b74c-453d-885f-5482d30e9acd"
        assert data["ativo"] is True
        assert "ultimo_login" in data

    def test_get_current_user_info_sem_token(self):
        """Deve retornar 401 quando não há token."""
        # Act
        response = self.client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 401

    # =====================================================
    # TESTES DE INTEGRAÇÃO REAL (OPCIONAL - PULE SE NÃO TIVER BANCO DE TESTE)
    # =====================================================

    @pytest.mark.skip(reason="Requer banco de dados de teste configurado")
    def test_login_integracao_real(self):
        """Teste real com banco de dados (pular se não tiver DB de teste)."""
        # Este teste só funciona se tiver um banco de teste com usuário real
        login_data = {
            "username": "usuario_real@email.com",
            "password": "senha_real"
        }
        
        response = self.client.post("/api/v1/auth/login", data=login_data)
        
        # Se o usuário existir, deve dar 200
        # Se não existir, vai dar 401 - ambos são aceitáveis
        assert response.status_code in [200, 401]