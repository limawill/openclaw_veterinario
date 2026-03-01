from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from yumi.models.veterinario import Veterinario
from yumi.schemas.schemas_veterinarios import VeterinarioCreate, VeterinarioUpdate
from yumi.services.veterinario_service import (
    atualizar_veterinario,
    create_veterinario,
    delete_veterinario,
    get_agendamentos_por_veterinario,
    get_veterinario_by_id,
    get_veterinarios_by_clinica,
)


class TestVeterinarioService:
    """Testes para o serviço de veterinários."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock da sessão do banco de dados."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def veterinario_data(self):
        """Dados de exemplo para criar veterinário."""
        return VeterinarioCreate(
            clinica_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            nome="Dr. João Silva",
            email="joao@email.com",
            especialidade="Clínica Geral"
        )
    
    @pytest.fixture
    def veterinario_existente(self):
        """Mock de um veterinário existente."""
        vet = Mock(spec=Veterinario)
        vet.id = "vet-123"
        vet.clinica_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        vet.nome = "Dr. João"
        vet.email = "joao@email.com"
        vet.especialidade = "Geral"
        vet.ativo = True
        vet.created_at = None
        return vet
    
    def test_create_veterinario_sucesso(self, mock_db, veterinario_data):
        """Testa criação de veterinário com sucesso."""
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act
        with patch('yumi.services.veterinario_service.gerar_uuid', return_value='new-vet'):
            resultado = create_veterinario(mock_db, veterinario_data)
        
        # Assert
        assert resultado.nome == veterinario_data.nome
        assert resultado.email == veterinario_data.email
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_create_veterinario_email_duplicado(self, mock_db, veterinario_data, veterinario_existente):
        """Testa erro ao criar veterinário com email duplicado."""
        # Arrange
        mock_db.query().filter().first.return_value = veterinario_existente
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_veterinario(mock_db, veterinario_data)
        
        assert exc_info.value.status_code == 400
        assert "email" in exc_info.value.detail.lower()
    
    def test_get_veterinario_by_id_sucesso(self, mock_db, veterinario_existente):
        """Testa busca de veterinário por ID."""
        # Arrange
        mock_db.query().filter().first.return_value = veterinario_existente
        
        # Act
        resultado = get_veterinario_by_id(mock_db, "vet-123")
        
        # Assert
        assert resultado.id == veterinario_existente.id
        assert resultado.nome == veterinario_existente.nome
    
    def test_get_veterinario_by_id_nao_encontrado(self, mock_db):
        """Testa erro quando veterinário não existe."""
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_veterinario_by_id(mock_db, "inexistente")
        
        assert exc_info.value.status_code == 404
    
    def test_get_veterinarios_by_clinica(self, mock_db, veterinario_existente):
        """Testa listagem de veterinários por clínica."""
        # Arrange
        mock_db.query().filter().all.return_value = [veterinario_existente]
        
        # Act
        resultado = get_veterinarios_by_clinica(mock_db, "clinica-123")
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0].id == veterinario_existente.id
    
    def test_atualizar_veterinario_sucesso(self, mock_db, veterinario_existente):
        """Testa atualização de veterinário."""
        # Arrange
        mock_db.query().filter().first.return_value = veterinario_existente
        update_data = VeterinarioUpdate(
            nome="Dr. João Atualizado",
            especialidade="Cirurgia"
        )
        
        # Act
        resultado = atualizar_veterinario(mock_db, "vet-123", update_data)
        
        # Assert
        assert resultado.nome == "Dr. João Atualizado"
        mock_db.commit.assert_called_once()
    
    def test_delete_veterinario_sucesso(self, mock_db, veterinario_existente):
        """Testa desativação de veterinário."""
        # Arrange
        mock_db.query().filter().first.return_value = veterinario_existente
        
        # Act
        resultado = delete_veterinario(mock_db, "vet-123")
        
        # Assert
        assert resultado.ativo is False
        mock_db.commit.assert_called_once()
    
    def test_get_agendamentos_por_veterinario_apenas_ativos_simples(self, mock_db):
        """Testa busca de agendamentos ativos (versão simplificada)."""
        # Arrange
        # 1. Mock da função get_veterinario_by_id
        mock_veterinario = Mock()
        mock_veterinario.id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        mock_veterinario.nome = "Dr. Teste"

        # 2. Mock direto da query de agendamentos
        mock_agendamento = Mock()
        mock_agendamento.status = "agendado"

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [mock_agendamento]
        mock_db.query.return_value = query_mock

        # Act
        with patch(
            'yumi.services.veterinario_service.get_veterinario_by_id',
            return_value=mock_veterinario
        ):
            resultado = get_agendamentos_por_veterinario(
                mock_db,
                "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                apenas_ativos=True
            )

        # Assert
        assert len(resultado) == 1
        assert resultado[0].status == "agendado"
