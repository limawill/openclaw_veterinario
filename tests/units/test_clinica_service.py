from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from yumi.models.clinica import Clinica
from yumi.schemas.schemas_clinica import ClinicaCreate, ClinicaUpdate
from yumi.services.clinica_service import (
    create_clinica,
    delete_clinica,
    get_clinica_by_id,
    listar_clinicas,
    update_clinica,
)


class TestClinicaService:
    """Testes para o serviço de clínicas."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock da sessão do banco de dados."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def clinica_data(self):
        """Dados de exemplo para criar clínica."""
        return ClinicaCreate(
            nome="Clínica Teste",
            endereco="Rua Teste, 123",
            configuracoes={"tempo_padrao_consulta": 30}
        )
    
    @pytest.fixture
    def clinica_existente(self):
        """Mock de uma clínica existente."""
        clinica = Mock(spec=Clinica)
        clinica.id = "clinica-123"
        clinica.nome = "Clínica Existente"
        clinica.endereco = "Rua X, 456"
        clinica.ativo = True
        clinica.configuracoes = {}
        clinica.created_at = None
        clinica.updated_at = None
        return clinica
    
    def test_create_clinica_sucesso(self, mock_db, clinica_data):
        """Testa criação de clínica com sucesso."""
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act
        with patch('yumi.services.clinica_service.gerar_uuid', return_value='new-id'):
            resultado = create_clinica(mock_db, clinica_data)
        
        # Assert
        assert resultado.nome == clinica_data.nome
        assert resultado.endereco == clinica_data.endereco
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_clinica_duplicada(self, mock_db, clinica_data, clinica_existente):
        """Testa erro ao criar clínica com nome duplicado."""
        # Arrange
        mock_db.query().filter().first.return_value = clinica_existente
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            create_clinica(mock_db, clinica_data)
        
        assert exc_info.value.status_code == 400
        assert "Já existe uma clínica com este nome" in exc_info.value.detail
        mock_db.add.assert_not_called()
    
    def test_listar_clinicas_vazia(self, mock_db):
        """Testa listagem quando não há clínicas."""
        # Arrange
        clinica_id = "clinica-test-123"
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        
        # Act
        resultado = listar_clinicas(mock_db, clinica_id)
        
        # Assert
        assert resultado == []
        mock_db.query.assert_called_once()
    
    def test_listar_clinicas_com_dados(self, mock_db, clinica_existente):
        """Testa listagem com clínicas existentes."""
        # Arrange
        clinica_id = clinica_existente.id
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [clinica_existente]
        mock_db.query.return_value = query_mock
        
        # Act
        resultado = listar_clinicas(mock_db, clinica_id)
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0].id == clinica_existente.id
    
    def test_get_clinica_by_id_encontrada(self, mock_db, clinica_existente):
        """Testa busca de clínica por ID com sucesso."""
        # Arrange
        mock_db.query().filter().first.return_value = clinica_existente
        
        # Act
        resultado = get_clinica_by_id(mock_db, "clinica-123")
        
        # Assert
        assert resultado.id == clinica_existente.id
        assert resultado.nome == clinica_existente.nome
    
    def test_get_clinica_by_id_nao_encontrada(self, mock_db):
        """Testa erro quando clínica não é encontrada."""
        # Arrange
        mock_db.query().filter().first.return_value = None
        mock_db.query().all.return_value = []
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_clinica_by_id(mock_db, "inexistente")
        
        assert exc_info.value.status_code == 404
        assert isinstance(exc_info.value.detail, dict)
        assert "mensagem" in exc_info.value.detail
    
    def test_update_clinica_sucesso(self, mock_db, clinica_existente):
        """Testa atualização de clínica com sucesso."""
        # Arrange
        mock_db.query().filter().first.return_value = clinica_existente
        update_data = ClinicaUpdate(
            nome="Nome Atualizado",
            endereco="Endereço Novo"
        )
        
        # Act
        resultado = update_clinica(mock_db, "clinica-123", update_data)
        
        # Assert
        assert resultado.nome == "Nome Atualizado"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_clinica_campos_opcionais(self, mock_db, clinica_existente):
        """Testa atualização apenas de campos fornecidos."""
        # Arrange
        mock_db.query().filter().first.return_value = clinica_existente
        update_data = ClinicaUpdate(nome="Só o Nome")
        
        # Act
        resultado = update_clinica(mock_db, "clinica-123", update_data)
        
        # Assert
        assert resultado.nome == "Só o Nome"
        # Endereço deve permanecer o mesmo
    
    def test_delete_clinica_sucesso(self, mock_db, clinica_existente):
        """Testa desativação de clínica."""
        # Arrange
        mock_db.query().filter().first.return_value = clinica_existente
        
        # Act
        resultado = delete_clinica(mock_db, "clinica-123")
        
        # Assert
        assert resultado.ativo is False
        mock_db.commit.assert_called_once()