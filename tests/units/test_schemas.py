from datetime import datetime

import pytest
from pydantic import ValidationError

from yumi.schemas.schemas_agendamento import AgendamentoCreate
from yumi.schemas.schemas_clinica import ClinicaCreate
from yumi.schemas.schemas_integracao import IntegracaoCreate
from yumi.schemas.schemas_usuario import UsuarioCreate
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


class TestUsuarioCreateSenhaForte:
    """Testes para validação de senha forte no schema UsuarioCreate."""

    BASE = {
        "clinica_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "nome": "João Silva",
        "email": "joao@email.com",
        "role": "admin",
        "ativo": True,
    }

    def _criar(self, senha: str):
        return UsuarioCreate(**self.BASE, senha=senha)

    def test_senha_valida(self):
        """Senha com todos os critérios deve ser aceita."""
        usuario = self._criar("Senha@123")
        assert usuario.senha == "Senha@123"

    def test_senha_sem_maiuscula(self):
        """Deve rejeitar senha sem letra maiúscula."""
        with pytest.raises(ValidationError) as exc:
            self._criar("senha@123")
        assert "maiúscula" in str(exc.value)

    def test_senha_sem_minuscula(self):
        """Deve rejeitar senha sem letra minúscula."""
        with pytest.raises(ValidationError) as exc:
            self._criar("SENHA@123")
        assert "minúscula" in str(exc.value)

    def test_senha_sem_numero(self):
        """Deve rejeitar senha sem número."""
        with pytest.raises(ValidationError) as exc:
            self._criar("Senha@abc")
        assert "número" in str(exc.value)

    def test_senha_sem_especial(self):
        """Deve rejeitar senha sem caractere especial."""
        with pytest.raises(ValidationError) as exc:
            self._criar("Senha1234")
        assert "especial" in str(exc.value)

    def test_senha_muito_curta(self):
        """Deve rejeitar senha com menos de 8 caracteres."""
        with pytest.raises(ValidationError):
            self._criar("S@1a")

    def test_senha_multiplos_erros(self):
        """Deve reportar todos os critérios faltando de uma vez."""
        # "somentex" tem 8 chars mas: sem maiúscula, sem número, sem especial
        with pytest.raises(ValidationError) as exc:
            self._criar("somentex")
        erros = str(exc.value)
        assert "maiúscula" in erros
        assert "número" in erros
        assert "especial" in erros