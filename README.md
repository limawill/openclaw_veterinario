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

## 📝 Configuração

As configurações estão centralizadas em [src/yumi/core/config.py](src/yumi/core/config.py):

- `APP_NAME` - Nome da aplicação
- `DATABASE_URL` - URL do banco de dados
- `HOST` / `PORT` - Configurações do servidor
- `SECRET_KEY` - Chave para autenticação

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
