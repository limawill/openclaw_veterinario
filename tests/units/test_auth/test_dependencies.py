from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from yumi.auth.dependencies import (
    get_current_admin,
    get_current_atendente,
    get_current_clinica_id,
    get_current_dev,
    get_current_user,
    verificar_mesma_clinica,
)


class TestGetCurrentUser:
    """Testes para função get_current_user."""

    @pytest.mark.asyncio
    @patch('yumi.auth.dependencies.decodificar_token_jwt')
    @patch('yumi.auth.dependencies.obter_usuario_por_id')
    async def test_get_current_user_sucesso(self, mock_obter_usuario, mock_decodificar):
        """Deve retornar usuário quando token válido."""
        # Arrange
        mock_decodificar.return_value = {"sub": "ef339b74-535d-4e2a-8102-d68c058eecad"}
        
        mock_usuario = Mock()
        mock_usuario.id = "ef339b74-535d-4e2a-8102-d68c058eecad"
        mock_usuario.email = "teste@email.com"
        mock_usuario.ativo = True
        mock_obter_usuario.return_value = mock_usuario
        
        # Act
        resultado = await get_current_user(token="token.valido", db=Mock())
        
        # Assert
        assert resultado == mock_usuario
        assert resultado.id == "ef339b74-535d-4e2a-8102-d68c058eecad"
        mock_decodificar.assert_called_once_with("token.valido")
        mock_obter_usuario.assert_called_once()

    @pytest.mark.asyncio
    @patch('yumi.auth.dependencies.decodificar_token_jwt')
    async def test_get_current_user_token_invalido(self, mock_decodificar):
        """Deve lançar 401 quando token é inválido."""
        # Arrange
        mock_decodificar.side_effect = JWTError("Token inválido")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="token.invalido", db=Mock())
        
        assert exc_info.value.status_code == 401
        assert "Token inválido" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('yumi.auth.dependencies.decodificar_token_jwt')
    async def test_get_current_user_sem_sub(self, mock_decodificar):
        """Deve lançar 401 quando token não contém 'sub'."""
        # Arrange
        mock_decodificar.return_value = {"email": "teste@email.com"}  # sem 'sub'
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="token.valido", db=Mock())
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch('yumi.auth.dependencies.decodificar_token_jwt')
    @patch('yumi.auth.dependencies.obter_usuario_por_id')
    async def test_get_current_user_usuario_inativo(self, mock_obter_usuario, mock_decodificar):
        """Deve lançar 403 quando usuário está inativo."""
        # Arrange
        mock_decodificar.return_value = {"sub": "ef339b74-535d-4e2a-8102-d68c058eecad"}
        
        mock_usuario = Mock()
        mock_usuario.ativo = False
        mock_obter_usuario.return_value = mock_usuario
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="token.valido", db=Mock())
        
        assert exc_info.value.status_code == 403
        assert "Usuário inativo" in exc_info.value.detail


class TestGetCurrentAdmin:
    """Testes para função get_current_admin."""

    @pytest.mark.asyncio
    async def test_get_current_admin_com_admin(self):
        """Deve retornar usuário quando role é admin."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "admin"
        
        # Act
        resultado = await get_current_admin(current_user=mock_usuario)
        
        # Assert
        assert resultado == mock_usuario

    @pytest.mark.asyncio
    async def test_get_current_admin_com_dev(self):
        """Deve retornar usuário quando role é dev (dev tem acesso admin)."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "dev"
        
        # Act
        resultado = await get_current_admin(current_user=mock_usuario)
        
        # Assert
        assert resultado == mock_usuario

    @pytest.mark.asyncio
    async def test_get_current_admin_com_atendente(self):
        """Deve lançar 403 quando role é atendente."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "atendente"
        mock_usuario.email = "atendente@email.com"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin(current_user=mock_usuario)
        
        assert exc_info.value.status_code == 403
        assert "Acesso negado" in exc_info.value.detail


class TestGetCurrentAtendente:
    """Testes para função get_current_atendente."""

    @pytest.mark.asyncio
    async def test_get_current_atendente_com_atendente(self):
        """Deve retornar usuário quando role é atendente."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "atendente"
        
        # Act
        resultado = await get_current_atendente(current_user=mock_usuario)
        
        # Assert
        assert resultado == mock_usuario

    @pytest.mark.asyncio
    async def test_get_current_atendente_com_admin(self):
        """Deve retornar usuário quando role é admin."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "admin"
        
        # Act
        resultado = await get_current_atendente(current_user=mock_usuario)
        
        # Assert
        assert resultado == mock_usuario

    @pytest.mark.asyncio
    async def test_get_current_atendente_com_role_invalida(self):
        """Deve lançar 403 quando role não tem permissão."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "visitante"
        mock_usuario.email = "visitante@email.com"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_atendente(current_user=mock_usuario)
        
        assert exc_info.value.status_code == 403


class TestGetCurrentDev:
    """Testes para função get_current_dev."""

    @pytest.mark.asyncio
    async def test_get_current_dev_com_dev(self):
        """Deve retornar usuário quando role é dev."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "dev"
        
        # Act
        resultado = await get_current_dev(current_user=mock_usuario)
        
        # Assert
        assert resultado == mock_usuario

    @pytest.mark.asyncio
    async def test_get_current_dev_com_admin(self):
        """Deve lançar 403 quando role é admin (não é dev)."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.role = "admin"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_dev(current_user=mock_usuario)
        
        assert exc_info.value.status_code == 403


class TestVerificarMesmaClinica:
    """Testes para função verificar_mesma_clinica."""

    @pytest.mark.asyncio
    async def test_mesma_clinica_ok(self):
        """Não deve lançar exceção quando clinica_id corresponde."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.clinica_id = "c320813a-abcc-458a-ad4a-8bd08aa27ec2"
        
        # Act & Assert (não deve lançar)
        await verificar_mesma_clinica("c320813a-abcc-458a-ad4a-8bd08aa27ec2", current_user=mock_usuario)

    @pytest.mark.asyncio
    async def test_clinica_diferente_lanca_403(self):
        """Deve lançar 403 quando clinica_id não corresponde."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.clinica_id = "c320813a-abcc-458a-ad4a-8bd08aa27ec2"
        mock_usuario.email = "usuario@email.com"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verificar_mesma_clinica("clinica-456", current_user=mock_usuario)
        
        assert exc_info.value.status_code == 403
        assert "Acesso negado a dados de outra clínica" in exc_info.value.detail


class TestGetCurrentClinicaId:
    """Testes para função get_current_clinica_id."""

    @pytest.mark.asyncio
    async def test_get_current_clinica_id_sucesso(self):
        """Deve retornar apenas o clinica_id do usuário."""
        # Arrange
        mock_usuario = Mock()
        mock_usuario.clinica_id = "c320813a-abcc-458a-ad4a-8bd08aa27ec2"
        
        # Act
        resultado = await get_current_clinica_id(current_user=mock_usuario)
        
        # Assert
        assert resultado == "c320813a-abcc-458a-ad4a-8bd08aa27ec2"