-- =====================================================
-- DESATIVAR FOREIGN KEYS TEMPORARIAMENTE
-- =====================================================
PRAGMA foreign_keys = OFF;

-- =====================================================
-- 1. PRIMEIRO: DROP DAS TABELAS (SE EXISTIREM) - ORDEM INVERSA DAS DEPENDÊNCIAS
-- =====================================================
DROP TABLE IF EXISTS chat_messages;

DROP TABLE IF EXISTS agendamento;

DROP TABLE IF EXISTS integracao;

DROP TABLE IF EXISTS chat_sessions;

DROP TABLE IF EXISTS refresh_tokens;

DROP TABLE IF EXISTS veterinario;

DROP TABLE IF EXISTS usuario;

DROP TABLE IF EXISTS clinica_funcionamento;

DROP TABLE IF EXISTS clinica;

-- =====================================================
-- 2. SEGUNDO: CRIAÇÃO DAS TABELAS - ORDEM CORRETA (SEM DEPENDÊNCIAS PRIMEIRO)
-- =====================================================

-- 2.1 TABELA CLINICA (base, não depende de ninguém)
CREATE TABLE IF NOT EXISTS clinica (
    id TEXT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    endereco TEXT,
    configuracoes TEXT,
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 TABELA HORARIO_FUNCIONAMENTO (depende de clinica)
CREATE TABLE IF NOT EXISTS clinica_funcionamento (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_abertura TIME NOT NULL,
    hora_fechamento TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE,
    UNIQUE (clinica_id, dia_semana)
);

-- 2.3 TABELA USUARIO (depende de clinica)
CREATE TABLE IF NOT EXISTS usuario (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    ultimo_login TIMESTAMP,
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE
);

-- 2.4 TABELA REFRESH_TOKENS (depende de usuario)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revogado BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE
);

-- 2.5 TABELA CHAT_SESSIONS (depende de clinica e usuario)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    canal VARCHAR(100) NOT NULL,
    usuario_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE
);

-- 2.6 TABELA CHAT_MESSAGES (depende de chat_sessions)
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK(role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
);

-- 2.7 TABELA VETERINARIO (depende de clinica)
CREATE TABLE IF NOT EXISTS veterinario (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    especialidade VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE
);

-- 2.8 TABELA INTEGRACAO (depende de clinica)
CREATE TABLE IF NOT EXISTS integracao (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    tipo_servico VARCHAR(50) NOT NULL CHECK (
        tipo_servico IN (
            'google_calendar',
            'whatsapp',
            'telegram'
        )
    ),
    credenciais TEXT NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE
);

-- 2.9 TABELA AGENDAMENTO (depende de clinica e veterinario)
CREATE TABLE IF NOT EXISTS agendamento (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    veterinario_id TEXT NOT NULL,
    nome_cliente VARCHAR(255) NOT NULL,
    telefone_cliente VARCHAR(20),
    nome_pet VARCHAR(255) NOT NULL,
    data_hora_inicio TIMESTAMP NOT NULL,
    data_hora_fim TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'agendado' CHECK (
        status IN (
            'agendado',
            'confirmado',
            'cancelado',
            'concluido'
        )
    ),
    origem VARCHAR(50) NOT NULL CHECK (
        origem IN (
            'chatbot',
            'manual',
            'whatsapp',
            'telegram'
        )
    ),
    id_evento_externo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES veterinario (id) ON DELETE RESTRICT,
    CHECK (
        data_hora_fim > data_hora_inicio
    )
);

-- =====================================================
-- 3. TERCEIRO: CRIAÇÃO DOS ÍNDICES (DEPOIS DAS TABELAS)
-- =====================================================

-- Índices para clinica_funcionamento
CREATE INDEX IF NOT EXISTS idx_funcionamento_clinica ON clinica_funcionamento (clinica_id);

-- Índices para usuario
CREATE INDEX IF NOT EXISTS idx_usuario_clinica ON usuario (clinica_id);

CREATE INDEX IF NOT EXISTS idx_usuario_email ON usuario (email);

-- Índices para refresh_tokens
CREATE INDEX IF NOT EXISTS idx_refresh_token_usuario ON refresh_tokens (usuario_id);

CREATE INDEX IF NOT EXISTS idx_refresh_token_token ON refresh_tokens (token);

-- Índices para veterinario
CREATE INDEX IF NOT EXISTS idx_veterinario_clinica ON veterinario (clinica_id);

-- Índices para integracao
CREATE INDEX IF NOT EXISTS idx_integracao_clinica ON integracao (clinica_id);

-- Índices para chat_sessions
CREATE INDEX IF NOT EXISTS idx_chat_session_clinica ON chat_sessions (clinica_id);

CREATE INDEX IF NOT EXISTS idx_chat_session_usuario ON chat_sessions (usuario_id);

CREATE INDEX IF NOT EXISTS idx_chat_session_canal ON chat_sessions (canal);

-- Índices para chat_messages
CREATE INDEX IF NOT EXISTS idx_chat_message_session ON chat_messages (session_id);

-- Índices para agendamento
CREATE INDEX IF NOT EXISTS idx_agendamento_clinica ON agendamento (clinica_id);

CREATE INDEX IF NOT EXISTS idx_agendamento_veterinario ON agendamento (veterinario_id);

CREATE INDEX IF NOT EXISTS idx_agendamento_data_inicio ON agendamento (data_hora_inicio);

CREATE INDEX IF NOT EXISTS idx_agendamento_status ON agendamento (status);

CREATE INDEX IF NOT EXISTS idx_agendamento_vet_data ON agendamento (
    veterinario_id,
    data_hora_inicio,
    data_hora_fim,
    status
);

-- =====================================================
-- 4. QUARTO: CRIAÇÃO DOS TRIGGERS
-- =====================================================

-- Trigger para clinica
DROP TRIGGER IF EXISTS trigger_update_clinica;

CREATE TRIGGER IF NOT EXISTS trigger_update_clinica 
    AFTER UPDATE ON clinica
    FOR EACH ROW
    BEGIN
        UPDATE clinica SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- Trigger para usuario
DROP TRIGGER IF EXISTS trigger_update_usuario;

CREATE TRIGGER IF NOT EXISTS trigger_update_usuario 
    AFTER UPDATE ON usuario
    FOR EACH ROW
    BEGIN
        UPDATE usuario SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- Trigger para veterinario
DROP TRIGGER IF EXISTS trigger_update_veterinario;

CREATE TRIGGER IF NOT EXISTS trigger_update_veterinario 
    AFTER UPDATE ON veterinario
    FOR EACH ROW
    BEGIN
        UPDATE veterinario SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- Trigger para integracao
DROP TRIGGER IF EXISTS trigger_update_integracao;

CREATE TRIGGER IF NOT EXISTS trigger_update_integracao 
    AFTER UPDATE ON integracao
    FOR EACH ROW
    BEGIN
        UPDATE integracao SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- Trigger para agendamento
DROP TRIGGER IF EXISTS trigger_update_agendamento;

CREATE TRIGGER IF NOT EXISTS trigger_update_agendamento 
    AFTER UPDATE ON agendamento
    FOR EACH ROW
    BEGIN
        UPDATE agendamento SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;

-- =====================================================
-- 5. REATIVAR FOREIGN KEYS
-- =====================================================
PRAGMA foreign_keys = ON;

-- =====================================================
-- 6. VERIFICAÇÃO (OPCIONAL)
-- =====================================================
SELECT 'Tabelas criadas com sucesso!' as Mensagem;