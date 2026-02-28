-- =====================================================
-- DESATIVAR FOREIGN KEYS TEMPORARIAMENTE
-- =====================================================
PRAGMA foreign_keys = OFF;

-- =====================================================
-- 1. PRIMEIRO: DROP DAS TABELAS (SE EXISTIREM) - ORDEM INVERSA DAS DEPENDÊNCIAS
-- =====================================================
DROP TABLE IF EXISTS agendamento;

DROP TABLE IF EXISTS integracao;

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
    role VARCHAR(50) NOT NULL CHECK (
        role IN ('admin', 'dev', 'atendente')
    ),
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE
);

-- 2.4 TABELA VETERINARIO (depende de clinica)
CREATE TABLE IF NOT EXISTS veterinario (
    id TEXT PRIMARY KEY,
    clinica_id TEXT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    especialidade VARCHAR(255),
    ativo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clinica_id) REFERENCES clinica (id) ON DELETE CASCADE
);

-- 2.5 TABELA INTEGRACAO (depende de clinica)
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

-- 2.6 TABELA AGENDAMENTO (depende de clinica e veterinario)
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

-- Índices para veterinario
CREATE INDEX IF NOT EXISTS idx_veterinario_clinica ON veterinario (clinica_id);

-- Índices para integracao
CREATE INDEX IF NOT EXISTS idx_integracao_clinica ON integracao (clinica_id);

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