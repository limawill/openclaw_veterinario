# 🐾 Yumi Agent - Sistema Veterinário

Agente virtual inteligente para gestão de clínicas veterinárias, desenvolvido com FastAPI e SQLite.

## 📋 Sobre o Projeto

O **Yumi Agent** é um sistema completo para gerenciamento de clínicas veterinárias, oferecendo funcionalidades de agendamento, gestão de veterinários, clientes e integrações com serviços externos como Google Calendar, WhatsApp e Telegram.

## 🚀 Tecnologias

- **Python 3.12+**
- **FastAPI** - Framework web moderno e rápido
- **SQLite** - Banco de dados leve e eficiente
- **Pydantic** - Validação de dados
- **Uvicorn** - Servidor ASGI de alta performance
- **SQLAlchemy** - ORM para banco de dados

## 📁 Estrutura do Projeto

```
openclaw_veterinario/
├── src/
│   └── yumi/
│       ├── api/           # Rotas da API
│       ├── core/          # Configurações e banco de dados
│       ├── database/      # Modelos SQL e inicialização
│       ├── models/        # Schemas Pydantic
│       └── utils/         # Utilitários
├── logs/                  # Arquivo de logs
├── pyproject.toml         # Dependências do projeto
├── run.py                 # Script de inicialização
└── README.md
```

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone <repository-url>
cd openclaw_veterinario
```

### 2. Instale as dependências

**Usando pip:**

```bash
pip install -e .
```

**Usando poetry:**

```bash
poetry install
```

### 3. Configure as variáveis de ambiente (opcional)

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=sqlite:///./src/yumi/database/yumi.db
HOST=0.0.0.0
PORT=9100
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
```

### 4. Inicialize o banco de dados

```bash
cd src/yumi/database
python init_db.py
```

Isso criará todas as tabelas necessárias. Você pode optar por adicionar dados de exemplo quando solicitado.

## ▶️ Como Usar

### Iniciar o servidor

**Método 1 - Script run.py:**

```bash
python run.py
```

**Método 2 - Diretamente com uvicorn:**

```bash
uvicorn yumi.main:app --host 0.0.0.0 --port 9100 --reload
```

O servidor estará disponível em: `http://localhost:9100`

### Acessar a documentação

- **Swagger UI**: http://localhost:9100/docs
- **ReDoc**: http://localhost:9100/redoc

## 🗄️ Banco de Dados

### Estrutura

O sistema possui as seguintes tabelas principais:

- **clinica** - Dados das clínicas
- **clinica_funcionamento** - Horários de funcionamento
- **usuario** - Usuários do sistema (admin, atendente, dev)
- **veterinario** - Cadastro de veterinários
- **agendamento** - Consultas agendadas
- **integracao** - Integrações externas (Google Calendar, WhatsApp, Telegram)

### Reinicializar o banco

Para resetar o banco de dados:

```bash
cd src/yumi/database
python init_db.py
```

## 🔌 Endpoints da API

### Principais Rotas

| Método | Endpoint  | Descrição              |
| ------ | --------- | ---------------------- |
| GET    | `/`       | Informações do projeto |
| GET    | `/health` | Health check da API    |
| GET    | `/docs`   | Documentação Swagger   |

### Exemplo de Resposta

**GET /**

```json
{
  "name": "Yumi Agent",
  "version": "0.1.0",
  "description": "Agente virtual para clínica veterinária",
  "environment": "development",
  "python_version": "3.12.0",
  "dependencies": [...]
}
```

## 🛠️ Desenvolvimento

### Ferramentas de Dev

- **Black** - Formatação de código
- **Ruff** - Linter rápido
- **Pytest** - Testes
- **Pre-commit** - Hooks de qualidade

### Rodar testes

```bash
pytest
```

### Formatar código

```bash
black src/
```

### Lint

```bash
ruff check src/
```

## �️ Desenvolvimento

### Ferramentas de Dev

- **Black** - Formatação de código
- **Ruff** - Linter rápido
- **Pytest** - Testes
- **Pre-commit** - Hooks de qualidade

### Rodar testes

```bash
pytest
```

### Formatar código

```bash
black src/
```

### Lint

```bash
ruff check src/
```

## 📋 Logging

### Overview

Sistema centralizado de logging com boas práticas, registrando todas as operações do projeto com formato padronizado.

**Formato de log:**

```
DATA:HORA - NÍVEL - MENSAGEM - ARQUIVO - FUNÇÃO
```

**Exemplo:**

```
28/02/2026 14:30:45 - INFO - Clínica criada com sucesso: Clínica Vet - clinica_service.py - create_clinica
```

### 🎯 Características

✅ **Centralizado** - Um único ponto de configuração  
✅ **Rotação automática** - Novo arquivo a cada 10MB  
✅ **Console colorido** - Cores diferentes para cada nível  
✅ **Arquivo de logs** - Histórico completo em `logs/`  
✅ **Sem dados sensíveis** - Configurado para não expor informações confidenciais  
✅ **Níveis apropriados** - DEBUG, INFO, WARNING, ERROR, CRITICAL

### 📦 Como Usar o Logger

#### 1. **Importar o logger**

```python
from yumi.core.logger import logger

# OU usar as funções auxiliares
from yumi.core.logger import log_info, log_error, log_warning, log_debug
```

#### 2. **Usar em Serviços (Lógica de Negócio)**

```python
from yumi.core.logger import logger

def criar_clinica(db: Session, clinica_data: ClinicaCreate):
    logger.debug(f"Iniciando criação de clínica: {clinica_data.nome}")

    try:
        # Lógica
        logger.info(f"Clínica criada: {clinica.nome} (ID: {clinica.id})")
        return clinica
    except Exception as e:
        logger.error(f"Erro ao criar clínica", exception=e)
        raise
```

#### 3. **Usar em Rotas (Endpoints)**

```python
from yumi.core.logger import logger

@router.post("/")
async def criar_clinica(clinica_data: ClinicaCreate, db: Session = Depends(get_db)):
    logger.info(f"POST /clinicas - Criando: {clinica_data.nome}")

    try:
        nova_clinica = clinica_service.create_clinica(db, clinica_data)
        return {"mensagem": "Sucesso", "clinica": nova_clinica}
    except Exception as e:
        logger.error(f"Erro no endpoint", exception=e)
        raise
```

#### 4. **Usar em Banco de Dados**

```python
from yumi.core.logger import logger

def get_db():
    db = SessionLocal()
    logger.debug("Sessão de banco aberta")
    try:
        yield db
    except Exception as e:
        logger.error("Erro no banco", exception=e)
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Sessão de banco fechada")
```

### 📊 Níveis de Log

| Nível        | Uso                                     | Exemplo                                |
| ------------ | --------------------------------------- | -------------------------------------- |
| **DEBUG**    | Informações detalhadas para diagnóstico | Inicio de função, valores de variáveis |
| **INFO**     | Eventos normais importantes             | Sucesso de operações, inicialização    |
| **WARNING**  | Situações inesperadas mas recuperáveis  | Duplicação, valores inválidos          |
| **ERROR**    | Erros que precisam atenção              | Exceções de banco, validação falhou    |
| **CRITICAL** | Erros graves do sistema                 | Falha na inicialização, perda de dados |

### 🗂️ Estrutura de Logs

```
logs/
├── yumi_20260228.log    # Logs do dia 28/02/2026
├── yumi_20260227.log    # Logs do dia anterior
└── yumi_20260227.log.1  # Arquivo comprimido antigo
```

Cada arquivo log comporta até 10MB. Quando atinge, um novo é criado.

### 🎨 Formato Completo

**Console (com cores):**

```
28/02/2026 14:30:45 - INFO - Clínica criada com sucesso - clinica_service.py - create_clinica
```

**Arquivo (completo):**

```
28/02/2026 14:30:45 - INFO - Clínica criada com sucesso - clinica_service.py - create_clinica - /media/Dados/openclaw_veterinario/src/yumi/services/clinica_service.py:35
```

### 🔧 Configuração Avançada

A configuração está em [src/yumi/core/logger.py](src/yumi/core/logger.py). Para evitar logs muito verbosos:

**Desenvolvimento** (UNSET = DEBUG):

```python
if settings.ENVIRONMENT == "development":
    logger.setLevel(logging.DEBUG)  # Mostra tudo
```

**Produção** (INFO e acima):

```python
else:
    logger.setLevel(logging.INFO)   # Menos verboso
```

### ⚠️ Boas Práticas

#### ✅ Faça:

```python
# Log com contexto claro
logger.info(f"Usuário criado: {usuario.id} - Email: {usuario.email}")

# Log de erros com exceção
try:
    executar()
except Exception as e:
    logger.error("Erro ao executar", exception=e)

# Log de debug para fluxo
logger.debug(f"Validando dados: {dados}")
```

#### ❌ Não faça:

```python
# Senhas, tokens, dados sensíveis
logger.info(f"Usuário: {usuario.senha}")

# Print simples
print("Executando algo")  # Use logger em vez disso

# Sem contexto
logger.info("Erro")  # Muito vago
```

### 📝 Exemplo Completo

```python
# services/clinica_service.py

from yumi.core.logger import logger

def create_clinica(db: Session, clinica_data: ClinicaCreate):
    """Cria uma nova clínica."""
    logger.debug(f"Iniciando criação de clínica: {clinica_data.nome}")

    # Verifica duplicidade
    clinica_existente = db.query(Clinica).filter(
        Clinica.nome == clinica_data.nome
    ).first()

    if clinica_existente:
        logger.warning(
            f"Tentativa de criar clínica duplicada: {clinica_data.nome} "
            f"(ID: {clinica_existente.id})"
        )
        raise HTTPException(status_code=400, detail="Clínica já existe")

    try:
        nova_clinica = Clinica(
            id=gerar_uuid(),
            nome=clinica_data.nome,
            endereco=clinica_data.endereco
        )

        db.add(nova_clinica)
        db.commit()
        db.refresh(nova_clinica)

        logger.info(
            f"Clínica criada com sucesso: {nova_clinica.nome} "
            f"(ID: {nova_clinica.id})"
        )
        return nova_clinica

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar clínica {clinica_data.nome}", exception=e)
        raise
```

### 🔍 Visualizar Logs

```bash
# Último arquivo de log
tail -f logs/yumi_*.log

# Ver últimas 50 linhas
tail -50 logs/yumi_*.log

# Buscar erro específico
grep "ERROR" logs/yumi_*.log

# Contar quantos erros houve
grep -c "ERROR" logs/yumi_*.log
```

## �📝 Configuração

As configurações estão centralizadas em [src/yumi/core/config.py](src/yumi/core/config.py):

- `APP_NAME` - Nome da aplicação
- `DATABASE_URL` - URL do banco de dados
- `HOST` / `PORT` - Configurações do servidor
- `SECRET_KEY` - Chave para autenticação

## 🚧 Pendências Técnicas

### 🔴 Token Blocklist no Logout (requer Redis)

**Status:** Não implementado  
**Prioridade:** Baixa (funcional para estudo, necessário antes de produção)

**Problema atual:**  
O logout revoga o `refresh_token` no banco, mas o `access_token` continua válido até seu vencimento natural (ex: 30 minutos). Um atacante com o access token capturado pode continuar usá-lo mesmo após o logout do usuário legítimo.

**Solução planejada:**

1. Adicionar campo `jti` (JWT ID — UUID único) no payload de cada `access_token` gerado em `security.py`
2. Criar `src/yumi/auth/token_blocklist.py` com `bloquear_jti()` e `jti_esta_bloqueado()`
3. No logout (`auth_routes.py`): extrair o `jti` do access token e adicioná-lo à blocklist
4. Em `dependencies.py`: verificar o `jti` na blocklist a cada requisição autenticada

**Armazenamento:**

- **Agora (SQLite/dev):** `set` Python em memória — se perde ao reiniciar o servidor
- **Produção (obrigatório):** Redis com TTL igual ao tempo de expiração do access token (`ACCESS_TOKEN_EXPIRE_MINUTES`)

**Dependência a instalar quando for implementar:**

```bash
poetry add redis
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Will Lima**

---

⭐ Feito com FastAPI e ❤️
