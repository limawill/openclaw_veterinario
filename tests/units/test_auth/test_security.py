from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from jose import JWTError

from yumi.auth.security import (
    criar_token_jwt,
    decodificar_token_jwt,
    extrair_dados_usuario_do_token,
    gerar_hash_senha,
    verificar_senha,
)


class TestHashSenha:
    """Testes para funções de hash de senha (bcrypt)."""

    def test_gerar_hash_senha_sucesso(self):
        """Deve gerar um hash válido para uma senha."""
        # Arrange
        senha = "minha_senha_123"
        
        # Act
        hash_resultado = gerar_hash_senha(senha)
        
        # Assert
        assert hash_resultado is not None
        assert isinstance(hash_resultado, str)
        assert hash_resultado.startswith("$2b$")  # Hash bcrypt começa com $2b$
        assert len(hash_resultado) > 50  # Tamanho típico de hash bcrypt

    def test_verificar_senha_correta(self):
        """Deve retornar True quando a senha corresponde ao hash."""
        # Arrange
        senha = "minha_senha_123"
        hash_senha = gerar_hash_senha(senha)
        
        # Act
        resultado = verificar_senha(senha, hash_senha)
        
        # Assert
        assert resultado is True

    def test_verificar_senha_incorreta(self):
        """Deve retornar False quando a senha NÃO corresponde ao hash."""
        # Arrange
        senha = "minha_senha_123"
        senha_errada = "senha_errada"
        hash_senha = gerar_hash_senha(senha)
        
        # Act
        resultado = verificar_senha(senha_errada, hash_senha)
        
        # Assert
        assert resultado is False

    def test_hashes_diferentes_para_mesma_senha(self):
        """
        Mesma senha deve gerar hashes diferentes (devido ao salt).
        Isso é importante para segurança.
        """
        # Arrange
        senha = "minha_senha_123"
        
        # Act
        hash1 = gerar_hash_senha(senha)
        hash2 = gerar_hash_senha(senha)
        
        # Assert
        assert hash1 != hash2
        assert verificar_senha(senha, hash1) is True
        assert verificar_senha(senha, hash2) is True

    def test_verificar_senha_com_hash_invalido(self):
        """Deve lidar graciosamente com hash inválido."""
        # Arrange
        senha = "teste"
        hash_invalido = "hash_invalido"
        
        # Act & Assert
        with pytest.raises(Exception):
            # Pode lançar exceção, mas não deve quebrar o teste
            verificar_senha(senha, hash_invalido)


class TestJWT:
    """Testes para funções de criação e validação de JWT."""

    def setup_method(self):
        """Configura dados comuns para os testes."""
        self.payload_teste = {
            "sub": "user-123",
            "clinica_id": "clinica-456",
            "role": "admin",
            "email": "teste@email.com"
        }

    def test_criar_token_jwt_sucesso(self):
        """Deve criar um token JWT válido."""
        # Act
        token = criar_token_jwt(self.payload_teste)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT tem 3 partes

    def test_decodificar_token_jwt_sucesso(self):
        """Deve decodificar um token JWT válido e retornar o payload."""
        # Arrange
        token = criar_token_jwt(self.payload_teste)
        
        # Act
        payload_decodificado = decodificar_token_jwt(token)
        
        # Assert
        assert payload_decodificado["sub"] == self.payload_teste["sub"]
        assert payload_decodificado["clinica_id"] == self.payload_teste["clinica_id"]
        assert payload_decodificado["role"] == self.payload_teste["role"]
        assert "exp" in payload_decodificado  # Deve ter data de expiração

    def test_token_expirado(self):
        """Deve lançar erro ao decodificar token expirado."""
        # Arrange
        with patch('yumi.auth.security.datetime') as mock_datetime:
            # Simula criação do token no passado
            mock_datetime.utcnow.return_value = datetime(2020, 1, 1)
            token = criar_token_jwt(self.payload_teste, expires_delta=timedelta(minutes=1))
        
        # Act & Assert
        with pytest.raises(JWTError):
            decodificar_token_jwt(token)

    def test_token_invalido(self):
        """Deve lançar erro ao decodificar token mal formatado."""
        # Arrange
        token_invalido = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token_invalido"
        
        # Act & Assert
        with pytest.raises(JWTError):
            decodificar_token_jwt(token_invalido)

    def test_token_com_assinatura_invalida(self):
        """Deve lançar erro ao decodificar token com assinatura inválida."""
        # Arrange
        token_valido = criar_token_jwt(self.payload_teste)
        # Modifica o token (altera último caractere)
        token_invalido = token_valido[:-5] + "xxxxx"
        
        # Act & Assert
        with pytest.raises(JWTError):
            decodificar_token_jwt(token_invalido)

    def test_criar_token_com_expiration_personalizado(self):
        """Deve permitir definir tempo de expiração personalizado."""
        # Arrange
        expires_delta = timedelta(hours=2)
        
        # Act
        token = criar_token_jwt(self.payload_teste, expires_delta=expires_delta)
        payload = decodificar_token_jwt(token)
        
        # Assert
        assert "exp" in payload


class TestExtrairDadosUsuario:
    """Testes para função extrair_dados_usuario_do_token."""

    def test_extrair_dados_sucesso(self):
        """Deve extrair corretamente os dados do usuário do payload."""
        # Arrange
        payload = {
            "sub": "user-123",
            "clinica_id": "clinica-456",
            "role": "admin",
            "email": "teste@email.com",
            "exp": 123456789
        }
        
        # Act
        dados = extrair_dados_usuario_do_token(payload)
        
        # Assert
        assert dados["id"] == "user-123"
        assert dados["clinica_id"] == "clinica-456"
        assert dados["role"] == "admin"

    def test_extrair_dados_campos_faltando(self):
        """Deve lançar erro se faltar campos obrigatórios."""
        # Arrange
        payload_incompleto = {
            "sub": "user-123",
            # clinica_id ausente
            "role": "admin"
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token não contém dados completos"):
            extrair_dados_usuario_do_token(payload_incompleto)

    def test_extrair_dados_campos_extra(self):
        """Deve ignorar campos extras no payload."""
        # Arrange
        payload_com_extra = {
            "sub": "user-123",
            "clinica_id": "clinica-456",
            "role": "admin",
            "email": "teste@email.com",
            "nome": "João Silva",  # Extra
            "iat": 123456789        # Extra
        }
        
        # Act
        dados = extrair_dados_usuario_do_token(payload_com_extra)
        
        # Assert
        assert dados["id"] == "user-123"
        assert dados["clinica_id"] == "clinica-456"
        assert dados["role"] == "admin"
        assert "email" not in dados  # Não deve incluir extras
        assert "nome" not in dados