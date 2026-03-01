from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from yumi.models.agendamento import Agendamento
from yumi.schemas.schemas_agendamento import AgendamentoCreate
from yumi.services.agendamento_service import (
    cancelar_agendamento,
    criar_agendamento,
    get_agendamento_by_id,
    listar_agendamentos,
    verificar_disponibilidade,
)


class TestAgendamentoService:
    """Testes para o serviço de agendamentos."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock da sessão do banco de dados."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def agendamento_data(self):
        """Dados de exemplo para criar agendamento."""
        return AgendamentoCreate(
            clinica_id="d53b7712-edf1-401e-a8f2-74fd58307dfa",
            veterinario_id="4287a1de-33d4-43c4-ada4-9e0776525531",
            nome_cliente="João Silva",
            telefone_cliente="11999999999",
            nome_pet="Rex",
            data_hora_inicio=datetime(2024, 3, 15, 10, 0),
            data_hora_fim=datetime(2024, 3, 15, 10, 30),
            origem="chatbot",
            status="agendado"
        )
    
    @pytest.fixture
    def mock_clinica(self):
        """Mock de clínica."""
        clinica = Mock()
        clinica.id = "d53b7712-edf1-401e-a8f2-74fd58307dfa"
        clinica.nome = "Clínica Teste"
        return clinica
    
    @pytest.fixture
    def mock_veterinario(self):
        """Mock de veterinário."""
        vet = Mock()
        vet.id = "4287a1de-33d4-43c4-ada4-9e0776525531"
        vet.nome = "Dr. João"
        return vet
    
    @patch('yumi.services.agendamento_service.get_clinica_by_id')
    @patch('yumi.services.agendamento_service.get_veterinario_by_id')
    @patch('yumi.services.agendamento_service._validar_horario_funcionamento')
    @patch('yumi.services.agendamento_service._validar_disponibilidade')
    def test_criar_agendamento_sucesso(
        self, 
        mock_validar_disp,
        mock_validar_horario,
        mock_get_vet,
        mock_get_clinica,
        mock_db,
        agendamento_data,
        mock_clinica,
        mock_veterinario
    ):
        """Testa criação de agendamento com sucesso."""
        # Arrange
        mock_get_clinica.return_value = mock_clinica
        mock_get_vet.return_value = mock_veterinario
        
        # Act
        with patch('yumi.services.agendamento_service.gerar_uuid', return_value='agend-123'):
            resultado = criar_agendamento(mock_db, agendamento_data)
        
        # Assert
        assert resultado["nome_cliente"] == agendamento_data.nome_cliente
        assert resultado["nome_veterinario"] == mock_veterinario.nome
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_listar_agendamentos_sem_filtros(self, mock_db):
        """Testa listagem sem filtros."""
        # Arrange
        mock_agendamentos = [Mock(), Mock()]
        query_mock = Mock()
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = mock_agendamentos
        query_mock.count.return_value = 2
        mock_db.query.return_value = query_mock
        
        # Act
        agendamentos, total = listar_agendamentos(mock_db)
        
        # Assert
        assert len(agendamentos) == 2
        assert total == 2
    
    def test_listar_agendamentos_com_filtro_clinica(self, mock_db):
        """Testa listagem filtrando por clínica."""
        # Arrange
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [Mock()]
        query_mock.count.return_value = 1
        mock_db.query.return_value = query_mock
        
        # Act
        agendamentos, total = listar_agendamentos(
            mock_db, 
            clinica_id="d53b7712-edf1-401e-a8f2-74fd58307dfa"
        )
        
        # Assert
        assert total == 1
    
    def test_get_agendamento_by_id_sucesso(self, mock_db):
        """Testa busca de agendamento por ID."""
        # Arrange
        mock_agendamento = Mock(spec=Agendamento)
        mock_agendamento.id = "agend-123"
        mock_db.query().filter().first.return_value = mock_agendamento
        
        # Act
        resultado = get_agendamento_by_id(mock_db, "agend-123")
        
        # Assert
        assert resultado.id == "agend-123"
    
    def test_cancelar_agendamento_sucesso(self, mock_db):
        """Testa cancelamento de agendamento."""
        # Arrange
        mock_agendamento = Mock(spec=Agendamento)
        mock_agendamento.status = "agendado"
        mock_db.query().filter().first.return_value = mock_agendamento
        
        # Act
        resultado = cancelar_agendamento(mock_db, "agend-123")
        
        # Assert
        assert resultado.status == "cancelado"
        mock_db.commit.assert_called_once()
    
    def test_verificar_disponibilidade(self, mock_db):
        """Testa verificação de disponibilidade."""
        # Arrange
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        
        # Act
        resultado = verificar_disponibilidade(
            mock_db,
            "4287a1de-33d4-43c4-ada4-9e0776525531",
            date(2024, 3, 15)
        )
        
        # Assert
        assert "horarios_ocupados" in resultado
        assert isinstance(resultado["horarios_ocupados"], list)
