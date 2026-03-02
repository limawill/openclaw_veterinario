from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from yumi.auth.auth_service import (
    _atualizar_ultimo_login,
    _get_usuario_por_email,
    _validar_senha,
    _validar_usuario_ativo,
    autenticar_usuario,
    obter_usuario_por_id,
)


class TestGetUsuarioPorEmail:
    """Testes para função auxiliar _get_usuario_por_email."""

    def test_busca_usuario_com_sucesso(self):
        """Deve retornar o usuário quando email existe."""
        # Arrange
        mock_db = Mock()
        mock_usuario = Mock()
        mock_usuario.email = "teste@email.com"
        
        # Configura o mock da query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_usuario
        mock_db.query.return_value = mock_query
        
        # Act
        resultado = _get_usuario_por_email(mock_db, "teste@email.com")
        
        # Assert
        assert resultado == mock_usuario
        mock_db.query.assert_called_once()

    def test_email_nao_encontrado(self):
        """Deve lançar HTTPException 401 quando email não existe."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            _get_usuario_por_email(mock_db, "naoexiste@email.com")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Credenciais inválidas"


class TestValidarUsuarioAtivo:
    """Testes para função auxiliar _validar_usuario_ativo."""

    def test_usuario_ativo_ok(self):
        """Não deve lançar exceção quando usuário está ativo."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.ativo = True
        
        # Act & Assert (não deve lançar exceção)
        _validar_usuario_ativo(mock_usuario)

    def test_usuario_inativo_lanca_403(self):
        """Deve lançar HTTPException 403 quando usuário está inativo."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.ativo = False
        mock_usuario.email = "inativo@email.com"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            _validar_usuario_ativo(mock_usuario)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Usuário inativo. Contate o administrador."


class TestValidarSenha:
    """Testes para função auxiliar _validar_senha."""

    @patch('yumi.auth.auth_service.verificar_senha')
    def test_senha_correta(self, mock_verificar_senha):
        """Não deve lançar exceção quando senha está correta."""
        # Arrange
        mock_verificar_senha.return_value = True
        
        # Act & Assert
        _validar_senha("senha123", "hash123")

    @patch('yumi.auth.auth_service.verificar_senha')
    def test_senha_incorreta_lanca_401(self, mock_verificar_senha):
        """Deve lançar HTTPException 401 quando senha está incorreta."""
        # Arrange
        mock_verificar_senha.return_value = False
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            _validar_senha("senha_errada", "hash123")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Credenciais inválidas"


class TestAtualizarUltimoLogin:
    """Testes para função auxiliar _atualizar_ultimo_login."""

    def test_atualiza_timestamp_com_sucesso(self):
        """Deve atualizar o campo ultimo_login e fazer commit."""
        # Arrange
        mock_db = Mock()
        mock_usuario = Mock()
        mock_usuario.ultimo_login = None
        
        # Act
        _atualizar_ultimo_login(mock_db, mock_usuario)
        
        # Assert
        assert mock_usuario.ultimo_login is not None
        assert isinstance(mock_usuario.ultimo_login, datetime)
        mock_db.commit.assert_called_once()


class TestAutenticarUsuario:
    """Testes para função principal autenticar_usuario."""

    def setup_method(self):
        """Configura mocks comuns para os testes."""
        self.mock_db = Mock()
        self.mock_usuario = Mock()
        self.mock_usuario.id = "user-123"
        self.mock_usuario.email = "teste@email.com"
        self.mock_usuario.clinica_id = "clinica-456"
        self.mock_usuario.role = "admin"
        self.mock_usuario.ativo = True
        self.mock_usuario.password_hash = "hash123"
        self.mock_usuario.ultimo_login = None

    @patch('yumi.auth.auth_service._get_usuario_por_email')
    @patch('yumi.auth.auth_service._validar_usuario_ativo')
    @patch('yumi.auth.auth_service._validar_senha')
    @patch('yumi.auth.auth_service._atualizar_ultimo_login')
    @patch('yumi.auth.auth_service.criar_token_jwt')
    def test_autenticar_usuario_sucesso(
        self,
        mock_criar_token,
        mock_atualizar_login,
        mock_validar_senha,
        mock_validar_ativo,
        mock_get_usuario
    ):
        """Deve autenticar com sucesso e retornar token."""
        # Arrange
        mock_get_usuario.return_value = self.mock_usuario
        mock_criar_token.return_value = "token.jwt.valido"
        
        # Act
        token = autenticar_usuario(
            self.mock_db,
            "teste@email.com",
            "senha123"
        )
        
        # Assert
        assert token == "token.jwt.valido"
        mock_get_usuario.assert_called_once_with(self.mock_db, "teste@email.com")
        mock_validar_ativo.assert_called_once_with(self.mock_usuario)
        mock_validar_senha.assert_called_once_with("senha123", "hash123")
        mock_atualizar_login.assert_called_once_with(self.mock_db, self.mock_usuario)
        mock_criar_token.assert_called_once()

    @patch('yumi.auth.auth_service._get_usuario_por_email')
    def test_autenticar_usuario_email_nao_encontrado(self, mock_get_usuario):
        """Deve propagar exceção quando email não encontrado."""
        # Arrange
        mock_get_usuario.side_effect = HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            autenticar_usuario(self.mock_db, "naoexiste@email.com", "senha123")
        
        assert exc_info.value.status_code == 401

    @patch('yumi.auth.auth_service._get_usuario_por_email')
    @patch('yumi.auth.auth_service._validar_usuario_ativo')
    def test_autenticar_usuario_inativo(self, mock_validar_ativo, mock_get_usuario):
        """Deve propagar exceção quando usuário inativo."""
        # Arrange
        mock_get_usuario.return_value = self.mock_usuario
        mock_validar_ativo.side_effect = HTTPException(
            status_code=403,
            detail="Usuário inativo"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            autenticar_usuario(self.mock_db, "teste@email.com", "senha123")
        
        assert exc_info.value.status_code == 403

    @patch('yumi.auth.auth_service._get_usuario_por_email')
    @patch('yumi.auth.auth_service._validar_usuario_ativo')
    @patch('yumi.auth.auth_service._validar_senha')
    def test_autenticar_usuario_senha_invalida(
        self,
        mock_validar_senha,
        mock_validar_ativo,
        mock_get_usuario
    ):
        """Deve propagar exceção quando senha inválida."""
        # Arrange
        mock_get_usuario.return_value = self.mock_usuario
        mock_validar_senha.side_effect = HTTPException(
            status_code=401,
            detail="Credenciais inválidas"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            autenticar_usuario(self.mock_db, "teste@email.com", "senha_errada")
        
        assert exc_info.value.status_code == 401


class TestObterUsuarioPorId:
    """Testes para função obter_usuario_por_id."""

    def test_obter_usuario_por_id_sucesso(self):
        """Deve retornar usuário quando ID existe."""
        # Arrange
        mock_db = Mock()
        mock_usuario = Mock()
        mock_usuario.id = "user-123"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_usuario
        mock_db.query.return_value = mock_query
        
        # Act
        resultado = obter_usuario_por_id(mock_db, "user-123")
        
        # Assert
        assert resultado == mock_usuario

    def test_obter_usuario_por_id_nao_encontrado(self):
        """Deve lançar HTTPException 404 quando ID não existe."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            obter_usuario_por_id(mock_db, "id-inexistente")
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Usuário não encontrado"