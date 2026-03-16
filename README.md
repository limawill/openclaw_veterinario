# Yumi Agent

Backend FastAPI para operação de clínica veterinária com:

- gestão de clínicas, usuários, veterinários e agendamentos
- autenticação JWT com refresh token
- integrações externas (Google Calendar, WhatsApp, Telegram)
- agente conversacional com memória de sessão
- integração com OpenClaw (WebSocket), com fallback local
- resposta em modo clássico (`/chat`) e streaming (`/chat/stream`)

## Visão Geral

O projeto segue arquitetura em camadas:

- `api`: rotas HTTP e validações de entrada/segurança
- `services`: regras de negócio e orquestração
- `auth`: autenticação, autorização e dependências de acesso
- `models` e `schemas`: persistência e contratos de dados
- `core`: configuração, banco, logger e limiter

Fluxo do chat (`/api/v1/agent/chat`):

1. valida usuário e isolamento multi-tenant
2. persiste mensagem do usuário
3. tenta OpenClaw se `USE_OPENCLAW=true`
4. em falha, usa `YumiAgent` local
5. persiste resposta final e retorna `ChatResponse`

Fluxo do streaming (`/api/v1/agent/chat/stream`):

1. valida usuário e isolamento multi-tenant
2. persiste mensagem do usuário
3. stream de chunks via OpenClaw quando habilitado
4. fallback local em chunk único quando necessário
5. persiste concatenação dos chunks enviados

## Stack Técnica

- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic / pydantic-settings
- SQLite (padrão)
- Uvicorn
- SlowAPI (rate limit)
- pytest / pytest-asyncio / httpx

## Estrutura do Repositório

```text
openclaw_veterinario/
├── src/yumi/
│   ├── api/
│   ├── agents/
│   ├── auth/
│   ├── core/
│   ├── database/
│   ├── llm/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
│   ├── integrations/
│   └── units/
├── pyproject.toml
└── README.md
```

## Configuração

As configurações ficam em `src/yumi/core/config.py` e podem ser sobrescritas por `.env`.

Principais variáveis:

```env
APP_NAME=Yumi Agent
APP_VERSION=0.1.0
ENVIRONMENT=development

HOST=0.0.0.0
PORT=9100
RELOAD=true

DATABASE_URL=sqlite:///./src/yumi/database/yumi.db
DATABASE_ECHO=false

SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CLAW_URL=http://100.87.246.16
CLAW_PORT=18789
CLAW_TIMEOUT=10
USE_OPENCLAW=false
```

## Instalação

### 1) Clonar

```bash
git clone <url-do-repositorio>
cd openclaw_veterinario
```

### 2) Ambiente virtual e dependências

Opção com `venv` + `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Opção com Poetry:

```bash
poetry install
poetry shell
```

### 3) Inicializar banco

```bash
PYTHONPATH=src python src/yumi/database/init_db.py
```

## Execução

```bash
PYTHONPATH=src uvicorn yumi.main:app --host 0.0.0.0 --port 9100 --reload
```

Endpoints úteis:

- Swagger: `http://localhost:9100/docs`
- ReDoc: `http://localhost:9100/redoc`
- Health: `http://localhost:9100/health`

## Endpoints Principais

Base principal:

- `GET /`
- `GET /health`
- `GET /info/python`
- `GET /info/sqlite`

Autenticação (`/api/v1/auth`):

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /me`

Domínio:

- Clínicas: `/api/v1/clinicas`
- Funcionamento: `/api/v1/clinicas/{clinica_id}/funcionamento`
- Usuários: `/api/v1/usuarios`
- Veterinários: `/api/v1/veterinarios`
- Agendamentos: `/api/v1/agendamentos`
- Integrações: `/api/v1/integracoes`

Agente (`/api/v1/agent`):

- `POST /chat` (resposta única)
- `POST /chat/stream` (stream de texto)

## Exemplos de Uso

### Login

```bash
curl -X POST "http://localhost:9100/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@clinica.com" \
  -d "password=123456"
```

### Chat padrão

```bash
curl -X POST "http://localhost:9100/api/v1/agent/chat" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "clinica_id": "170a7399-4b47-4ad1-a10b-a8ac69b4a166",
    "mensagem": "Meu cachorro está vomitando há dois dias"
  }'
```

### Chat streaming

Use `--no-buffer` para ver os chunks em tempo real.

```bash
curl --no-buffer -X POST "http://localhost:9100/api/v1/agent/chat/stream" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "clinica_id": "170a7399-4b47-4ad1-a10b-a8ac69b4a166",
    "mensagem": "Quais horários você tem para amanhã?"
  }'
```

## OpenClaw e Fallback

Com `USE_OPENCLAW=true`:

- `/chat` tenta `OpenClawClient.send_prompt(...)`
- `/chat/stream` tenta `OpenClawClient.stream_prompt(...)`

Fallback automático para `YumiAgent` ocorre quando:

- OpenClaw está desabilitado (`USE_OPENCLAW=false`)
- timeout
- falha de conexão WebSocket
- erro inesperado no fluxo OpenClaw

## Segurança

- autenticação JWT bearer
- refresh token com rotação
- proteção multi-tenant por `clinica_id`
- rate limit em login (`5/minute`)

## Logs

Logger central em `src/yumi/core/logger.py` com:

- saída em console
- arquivo rotativo em `logs/`
- níveis de severidade (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

## Testes

Executar suíte completa:

```bash
PYTHONPATH=src pytest -q
```

Executar apenas streaming:

```bash
PYTHONPATH=src pytest -q tests/units/test_chat_stream_service.py tests/integrations/test_chat_stream_route.py
```

## Qualidade de Código

```bash
black src tests
ruff check src tests
```

## Status Atual

O projeto está com fluxo de chat e streaming funcionando com fallback operacional, preparado para evolução das integrações com OpenClaw e canais externos.
