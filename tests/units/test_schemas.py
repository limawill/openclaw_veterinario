from datetime import datetime

import pytest
from pydantic import ValidationError

from yumi.schemas.schemas_agendamento import AgendamentoCreate
from yumi.schemas.schemas_clinica import ClinicaCreate
from yumi.schemas.schemas_integracao import IntegracaoCreate
from yumi.schemas.schemas_veterinarios import VeterinarioCreate


class TestSchemas:
    """Testes de validação dos schemas Pydantic."""
    
    def test_clinica_create_valid(self):
        """Testa criação válida de schema de clínica."""
        # Act
        clinica = ClinicaCreate(
            nome="Clínica Teste",
            endereco="Rua Teste, 123"
        )
        
        # Assert
        assert clinica.nome == "Clínica Teste"
    
    def test_clinica_create_nome_muito_curto(self):
        """Testa validação de nome curto."""
        # Act & Assert
        with pytest.raises(ValidationError):
            ClinicaCreate(nome="AB")
    
    def test_veterinario_create_valid(self):
        """Testa criação válida de veterinário."""
        # Act
        vet = VeterinarioCreate(
            clinica_id="751f3cba-fe70-4da3-b8ab-f7029196b352",
            nome="Dr. João",
            especialidade="Clínica Geral",
            email="joao@email.com"
        )
        
        # Assert
        assert vet.email == "joao@email.com"
    
    def test_veterinario_create_email_invalido(self):
        """Testa validação de email."""
        # Act & Assert
        with pytest.raises(ValidationError):
            VeterinarioCreate(
                clinica_id="123",
                nome="Dr. João",
                email="email_invalido"
            )
    
    def test_agendamento_create_valid(self):
        """Testa criação válida de agendamento."""
        # Act
        agendamento = AgendamentoCreate(
            clinica_id="clinica-123",
            veterinario_id="vet-123",
            nome_cliente="João",
            nome_pet="Rex",
            data_hora_inicio=datetime(2024, 3, 15, 10, 0),
            data_hora_fim=datetime(2024, 3, 15, 10, 30),
            origem="chatbot"
        )
        
        # Assert
        assert agendamento.nome_cliente == "João"
    
    def test_integracao_tipo_servico_invalido(self):
        """Testa validação de tipo de serviço."""
        # Act & Assert
        with pytest.raises(ValidationError):
            IntegracaoCreate(
                clinica_id="clinica-123",
                tipo_servico="servico_invalido",
                credenciais={}
            )