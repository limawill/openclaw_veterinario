from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from yumi.main import app


@pytest.fixture
def client():
    """Cliente de teste da API."""
    return TestClient(app)


class TestAgendamentoRoutes:
    """Testes para endpoints de agendamentos."""
    
    @patch('yumi.api.agendamento_routes.agendamento_service.criar_agendamento')
    def test_criar_agendamento_sucesso(self, mock_criar, client):
        """Testa POST /api/v1/agendamentos."""
        # Arrange
        mock_agendamento = Mock()
        mock_agendamento.id = "c697fa71-58b4-4cea-b5b6-d2aa68c3208f"
        mock_agendamento.clinica_id = "f7fc5f9b-6d8e-430d-9196-adc6d1af5887"
        mock_agendamento.veterinario_id = "439481c1-74a7-4dac-8d52-5bdd1c12da9f"
        mock_agendamento.nome_cliente = "João Silva"
        mock_agendamento.telefone_cliente = "11999999999"
        mock_agendamento.nome_pet = "Rex"
        mock_agendamento.data_hora_inicio = datetime(2024, 3, 15, 10, 0, 0)
        mock_agendamento.data_hora_fim = datetime(2024, 3, 15, 10, 30, 0)
        mock_agendamento.status = "agendado"
        mock_agendamento.origem = "chatbot"
        mock_agendamento.id_evento_externo = None
        mock_agendamento.created_at = datetime.now()
        mock_agendamento.updated_at = datetime.now()
        mock_agendamento.nome_veterinario = "Dr. Silva"
        mock_agendamento.nome_clinica = "Clínica Teste"
        mock_criar.return_value = mock_agendamento
        payload = {
            "clinica_id": "f7fc5f9b-6d8e-430d-9196-adc6d1af5887",
            "veterinario_id": "439481c1-74a7-4dac-8d52-5bdd1c12da9f",
            "nome_cliente": "João Silva",
            "nome_pet": "Rex",
            "data_hora_inicio": "2024-03-15T10:00:00",
            "data_hora_fim": "2024-03-15T10:30:00",
            "origem": "chatbot"
        }
        
        # Act
        response = client.post("/api/v1/agendamentos", json=payload)
        
        # Assert
        assert response.status_code == 201
    
    @patch('yumi.api.agendamento_routes.agendamento_service.listar_agendamentos')
    def test_listar_agendamentos_com_filtros(self, mock_listar, client):
        """Testa GET /api/v1/agendamentos com filtros."""
        # Arrange
        mock_listar.return_value = ([], 0)
        
        # Act
        response = client.get(
            "/api/v1/agendamentos",
            params={
                "clinica_id": "f7fc5f9b-6d8e-430d-9196-adc6d1af5887",
                "status": "agendado"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["total"] == 0
    
    @patch('yumi.api.agendamento_routes.agendamento_service.cancelar_agendamento')
    def test_cancelar_agendamento_sucesso(self, mock_cancelar, client):
        """Testa PATCH /api/v1/agendamentos/{id}/cancelar."""
        # Arrange
        mock_agendamento = Mock()
        mock_agendamento.id = "c697fa71-58b4-4cea-b5b6-d2aa68c3208f"
        mock_agendamento.clinica_id = "f7fc5f9b-6d8e-430d-9196-adc6d1af5887"
        mock_agendamento.veterinario_id = "439481c1-74a7-4dac-8d52-5bdd1c12da9f"
        mock_agendamento.nome_cliente = "João Silva"
        mock_agendamento.telefone_cliente = "11999999999"
        mock_agendamento.nome_pet = "Rex"
        mock_agendamento.data_hora_inicio = datetime(2024, 3, 15, 10, 0, 0)
        mock_agendamento.data_hora_fim = datetime(2024, 3, 15, 10, 30, 0)
        mock_agendamento.status = "cancelado"
        mock_agendamento.origem = "chatbot"
        mock_agendamento.id_evento_externo = None
        mock_agendamento.created_at = datetime.now()
        mock_agendamento.updated_at = datetime.now()
        mock_agendamento.nome_veterinario = "Dr. Silva"
        mock_agendamento.nome_clinica = "Clínica Teste"
        mock_cancelar.return_value = mock_agendamento
        
        # Act
        response = client.patch("/api/v1/agendamentos/c697fa71-58b4-4cea-b5b6-d2aa68c3208f/cancelar")
        
        # Assert
        assert response.status_code == 200