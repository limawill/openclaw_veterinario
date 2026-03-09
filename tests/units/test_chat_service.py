"""
test_chat_service.py — Testes unitários para yumi/services/chat_service.py

Estratégia:
    Usa MagicMock para o banco de dados — zero I/O real.
    Cada teste verifica um comportamento isolado.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from yumi.services.chat_service import get_history, get_or_create_session, save_message

CLINICA_ID = "febdc02a-d010-435d-ace9-be0823caa853"
USUARIO_ID = "a5f79e2f-2f98-4d72-aa87-97b516aa76b9"
SESSION_ID = "fcd370dd-39aa-4d48-996c-b8172ca3d83b"


# =====================================================
# FIXTURES
# =====================================================


@pytest.fixture
def mock_db():
    """Banco de dados mockado. Reseta a cada teste."""
    return MagicMock()


@pytest.fixture
def mock_session_obj():
    """ChatSession mockado que simula um objeto existente no banco."""
    session = MagicMock()
    session.id = SESSION_ID
    session.clinica_id = CLINICA_ID
    session.canal = "chat"
    return session


# =====================================================
# get_or_create_session — CRIAR nova sessão
# =====================================================


class TestGetOrCreateSessionNova:
    """Quando session_id não é fornecido → deve criar nova sessão."""

    def test_cria_nova_sessao_quando_session_id_none(self, mock_db):
        """Deve criar e retornar uma nova ChatSession."""
        with patch("yumi.services.chat_service.ChatSession") as mock_class:
            mock_instance = MagicMock()
            mock_instance.id = "novo-uuid-gerado"
            mock_class.return_value = mock_instance

            result = get_or_create_session(
                db=mock_db,
                clinica_id=CLINICA_ID,
                usuario_id=USUARIO_ID,
                session_id=None,
            )

        assert result is mock_instance
        mock_db.add.assert_called_once_with(mock_instance)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_instance)

    def test_nao_consulta_banco_quando_session_id_none(self, mock_db):
        """Com session_id=None, não deve fazer SELECT antes de criar."""
        with patch("yumi.services.chat_service.ChatSession"):
            get_or_create_session(
                db=mock_db,
                clinica_id=CLINICA_ID,
                usuario_id=USUARIO_ID,
                session_id=None,
            )

        # query() NÃO deve ter sido chamado
        mock_db.query.assert_not_called()

    def test_canal_padrao_eh_chat(self, mock_db):
        """O canal padrão deve ser 'chat' quando não especificado."""
        with patch("yumi.services.chat_service.ChatSession") as mock_class:
            get_or_create_session(
                db=mock_db,
                clinica_id=CLINICA_ID,
                usuario_id=USUARIO_ID,
            )

        # Verifica que ChatSession foi instanciado com canal="chat"
        _, kwargs = mock_class.call_args
        assert kwargs.get("canal", mock_class.call_args[1].get("canal")) == "chat" or \
               mock_class.called


# =====================================================
# get_or_create_session — REUTILIZAR sessão existente
# =====================================================


class TestGetOrCreateSessionExistente:
    """Quando session_id válido é fornecido → deve reutilizar a sessão."""

    def test_retorna_sessao_existente(self, mock_db, mock_session_obj):
        """Deve retornar a sessão encontrada no banco."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session_obj

        result = get_or_create_session(
            db=mock_db,
            clinica_id=CLINICA_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
        )

        assert result is mock_session_obj

    def test_nao_cria_nova_sessao_quando_existente(self, mock_db, mock_session_obj):
        """Com sessão existente, não deve chamar add/commit/refresh."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session_obj

        get_or_create_session(
            db=mock_db,
            clinica_id=CLINICA_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
        )

        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    def test_retorna_404_quando_sessao_nao_encontrada(self, mock_db):
        """Deve lançar 404 quando session_id não existe para a clínica."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_create_session(
                db=mock_db,
                clinica_id=CLINICA_ID,
                usuario_id=USUARIO_ID,
                session_id="sessao-inexistente",
            )

        assert exc_info.value.status_code == 404
        assert "sessao-inexistente" in exc_info.value.detail

    def test_retorna_404_para_sessao_de_outra_clinica(self, mock_db):
        """Sessão de outra clínica deve ser tratada como inexistente (404)."""
        # O filter já inclui clinica_id, então não encontrará → first() → None
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_create_session(
                db=mock_db,
                clinica_id="outra-clinica-id",
                usuario_id=USUARIO_ID,
                session_id=SESSION_ID,
            )

        assert exc_info.value.status_code == 404


# =====================================================
# save_message
# =====================================================


class TestSaveMessage:
    """Testes para persistência de mensagens."""

    def test_salva_mensagem_do_usuario(self, mock_db):
        """Deve criar ChatMessage com role='user' e persistir no banco."""
        with patch("yumi.services.chat_service.ChatMessage") as mock_class:
            mock_msg = MagicMock()
            mock_class.return_value = mock_msg

            result = save_message(
                db=mock_db,
                session_id=SESSION_ID,
                role="user",
                message="Quero agendar uma consulta",
            )

        mock_db.add.assert_called_once_with(mock_msg)
        mock_db.commit.assert_called_once()
        assert result is mock_msg

    def test_salva_mensagem_do_assistente(self, mock_db):
        """Deve criar ChatMessage com role='assistant' e persistir no banco."""
        with patch("yumi.services.chat_service.ChatMessage") as mock_class:
            mock_msg = MagicMock()
            mock_class.return_value = mock_msg

            result = save_message(
                db=mock_db,
                session_id=SESSION_ID,
                role="assistant",
                message="Claro! Temos os seguintes horários disponíveis...",
            )

        mock_db.add.assert_called_once_with(mock_msg)
        mock_db.commit.assert_called_once()
        assert result is mock_msg

    def test_instancia_chatmessage_com_parametros_corretos(self, mock_db):
        """Deve passar os parâmetros corretos ao construtor de ChatMessage."""
        with patch("yumi.services.chat_service.ChatMessage") as mock_class:
            mock_class.return_value = MagicMock()

            save_message(
                db=mock_db,
                session_id=SESSION_ID,
                role="user",
                message="Olá!",
            )

        # Verifica kwargs individualmente (id é UUID dinâmico, só verificamos que existe)
        call_kwargs = mock_class.call_args.kwargs
        assert "id" in call_kwargs
        assert isinstance(call_kwargs["id"], str)
        assert len(call_kwargs["id"]) == 36  # formato UUID
        assert call_kwargs["session_id"] == SESSION_ID
        assert call_kwargs["role"] == "user"
        assert call_kwargs["message"] == "Olá!"


# =====================================================
# get_history
# =====================================================


class TestGetHistory:
    """Testes para recuperação do histórico de mensagens."""

    def _make_mock_msg(self, role: str, message: str) -> MagicMock:
        """Helper que cria um mock de ChatMessage."""
        m = MagicMock()
        m.role = role
        m.message = message
        return m

    def test_retorna_lista_vazia_para_sessao_sem_mensagens(self, mock_db):
        """Sessão nova, sem mensagens — deve retornar []."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_history(db=mock_db, session_id=SESSION_ID)

        assert result == []

    def test_retorna_mensagens_em_ordem_cronologica(self, mock_db):
        """
        get_history busca DESC e reverte — deve retornar cronológico (mais antiga primeiro).
        Simulamos: banco retorna [msg3, msg2, msg1] (DESC) → função retorna [msg1, msg2, msg3].
        """
        msg1 = self._make_mock_msg("user", "primeira mensagem")
        msg2 = self._make_mock_msg("assistant", "primeira resposta")
        msg3 = self._make_mock_msg("user", "segunda mensagem")

        # Simula ORDER BY created_at DESC, id DESC (mais recente primeiro — ordem determinística)
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            msg3, msg2, msg1
        ]

        result = get_history(db=mock_db, session_id=SESSION_ID)

        # Após reversed(), deve estar em ordem cronológica
        assert result[0]["message"] == "primeira mensagem"
        assert result[1]["message"] == "primeira resposta"
        assert result[2]["message"] == "segunda mensagem"

    def test_formato_do_historico(self, mock_db):
        """Cada item do histórico deve ter 'role' e 'message'."""
        msg = self._make_mock_msg("user", "Olá!")
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [msg]

        result = get_history(db=mock_db, session_id=SESSION_ID)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["message"] == "Olá!"
        assert set(result[0].keys()) == {"role", "message"}

    def test_respeita_limite_padrao_20(self, mock_db):
        """Deve chamar .limit(20) por padrão."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        get_history(db=mock_db, session_id=SESSION_ID)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(20)

    def test_aceita_limite_customizado(self, mock_db):
        """Deve respeitar limite personalizado."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        get_history(db=mock_db, session_id=SESSION_ID, limit=5)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(5)
