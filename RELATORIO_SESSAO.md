# Relatório de Sessão — Yumi Agent

> Gerado em: 06/03/2026  
> Finalidade: Relatório de continuidade para o agente de gerência do projeto

---

## 1. Contexto do Projeto

**Nome:** Yumi Agent  
**Stack:** Python 3.12, FastAPI, SQLAlchemy, SQLite (migração para Postgres/MySQL planejada), Poetry  
**Finalidade atual:** CRUD de estudo/pesquisa para sistema de gestão de clínicas veterinárias  
**Estrutura de pastas relevante:**

```
src/yumi/
├── api/           # Rotas REST por domínio
├── auth/          # Sistema de autenticação (JWT)
├── core/          # Config, banco, logger, limiter
├── database/      # models.sql + init_db.py
├── models/        # Models SQLAlchemy
├── schemas/       # Schemas Pydantic por domínio
├── services/      # Regras de negócio
└── utils/         # Ferramentas e UUID

tests/
├── integrations/  # Testes de rota (TestClient)
└── units/         # Testes unitários com mock
```

---

## 2. O que foi implementado nesta sessão

Toda a sessão focou em **melhorar e completar o sistema de autenticação**. Abaixo cada item com os arquivos afetados.

---

### 2.1 Validação de senha forte

**Problema:** `UsuarioCreate` não tinha campo `senha` e o `create_usuario` nunca gerava o `password_hash`.

**Arquivos alterados:**

| Arquivo                                | O que mudou                                                                                                                      |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `src/yumi/schemas/schemas_usuario.py`  | Adicionado campo `senha: str` com `min_length=8` e `@field_validator` exigindo maiúscula, minúscula, número e caractere especial |
| `src/yumi/services/usuario_service.py` | `create_usuario()` agora chama `gerar_hash_senha(usuario_data.senha)` e popula `password_hash` no model                          |

---

### 2.2 Refresh Token (Abordagem Stateful — banco de dados)

**Problema:** Sistema tinha apenas `access_token`. Ao expirar, o usuário precisava logar novamente.

**Novo arquivo criado:**

| Arquivo                            | Descrição                                       |
| ---------------------------------- | ----------------------------------------------- |
| `src/yumi/models/refresh_token.py` | Model SQLAlchemy para a tabela `refresh_tokens` |

**Arquivos alterados:**

| Arquivo                         | O que mudou                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/yumi/database/models.sql`  | Nova tabela `refresh_tokens` com colunas: `id`, `usuario_id` (FK → usuario), `token`, `expires_at`, `revogado`, `created_at`. `DROP TABLE IF EXISTS refresh_tokens` adicionado na ordem correta (antes de `usuario`)                                                                                                                                                          |
| `src/yumi/models/__init__.py`   | `RefreshToken` registrado junto aos outros models                                                                                                                                                                                                                                                                                                                             |
| `src/yumi/core/config.py`       | `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` adicionado                                                                                                                                                                                                                                                                                                                               |
| `src/yumi/auth/security.py`     | Nova função `criar_refresh_token(dados)`: gera JWT com `type=refresh`, validade de 7 dias                                                                                                                                                                                                                                                                                     |
| `src/yumi/auth/auth_service.py` | 3 novas funções: `salvar_refresh_token()`, `renovar_tokens()` (com rotação de tokens), `revogar_refresh_token()`. `autenticar_usuario()` agora retorna `dict` com `access_token`, `refresh_token` e `usuario` (antes retornava só a string do access token). Import de `decodificar_token_jwt` movido para o topo do módulo (necessário para o `@patch` funcionar nos testes) |
| `src/yumi/auth/auth_routes.py`  | Novos schemas: `UsuarioInfo`, `RefreshRequest`, `LogoutRequest`. `TokenResponse` ganhou campos `refresh_token` e `usuario`. Novos endpoints: `POST /api/v1/auth/refresh` e `POST /api/v1/auth/logout` (logout real que revoga o refresh token no banco)                                                                                                                       |

---

### 2.3 Login retorna dados do usuário

**Problema:** Frontend precisava de 2 requisições (login + /me) para obter os dados do usuário.

**Arquivos alterados:**

| Arquivo                         | O que mudou                                                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/yumi/auth/auth_service.py` | `autenticar_usuario()` retorna dict com chave `usuario` contendo `id`, `nome`, `email`, `role`, `clinica_id`                                                  |
| `src/yumi/auth/auth_routes.py`  | Schema `TokenResponse` inclui campo `usuario: UsuarioInfo \| None = None`. O `/login` preenche esse campo. O `/refresh` deixa `usuario=None` intencionalmente |

---

### 2.4 Rate Limiting no endpoint de login

**Problema:** Sem proteção contra ataques de força bruta.

**Dependência instalada:**

```bash
poetry add slowapi
# instala também: wrapt, deprecated, limits
```

**Novo arquivo criado:**

| Arquivo                    | Descrição                                                                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `src/yumi/core/limiter.py` | Instância global do `Limiter` usando IP do cliente como chave. Criado aqui para evitar import circular entre `main.py` e `auth_routes.py` |

**Arquivos alterados:**

| Arquivo                        | O que mudou                                                                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/yumi/main.py`             | `app.state.limiter = limiter` e `app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)`                                  |
| `src/yumi/auth/auth_routes.py` | `@limiter.limit("5/minute")` no endpoint `/login`. `request: Request` adicionado como primeiro parâmetro da função (obrigatório pelo slowapi) |

---

### 2.5 Correção no `database.py`

**Problema:** `init_db.py` tentava importar `get_connection` e `get_db_path_from_url` que não existiam.

**Arquivo alterado:**

| Arquivo                     | O que mudou                                                                                                                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/yumi/core/database.py` | Adicionadas funções `get_db_path_from_url()` (extrai path do SQLite a partir da `DATABASE_URL`) e `get_connection()` (retorna conexão `sqlite3` pura para uso no `init_db.py`) |

---

### 2.6 Testes

**Cobertura expandida de 97 → 124 testes, todos passando.**

**Testes atualizados (quebrariam sem correção):**

| Arquivo                                                                       | Motivo da atualização                                                                                 |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `tests/integrations/test_auth_routes.py::test_login_sucesso`                  | Mock passou a retornar dict em vez de string                                                          |
| `tests/integrations/test_auth_routes.py::test_logout`                         | Logout agora exige body `{"refresh_token": "..."}`                                                    |
| `tests/units/test_auth/test_auth_service.py::test_autenticar_usuario_sucesso` | Adicionados mocks de `criar_refresh_token` e `salvar_refresh_token`; assert mudou de string para dict |

**Testes novos criados:**

| Arquivo                                      | Classe                        | Cenários                                                                                           |
| -------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| `tests/units/test_auth/test_auth_service.py` | `TestSalvarRefreshToken`      | Persiste registro com campos corretos                                                              |
| `tests/units/test_auth/test_auth_service.py` | `TestRevogarRefreshToken`     | Token existente, já revogado, não encontrado                                                       |
| `tests/units/test_auth/test_auth_service.py` | `TestRenovarTokens`           | Sucesso, JWT inválido, type errado, token revogado, não encontrado no banco                        |
| `tests/units/test_auth/test_security.py`     | `TestCriarRefreshToken`       | JWT válido, type=refresh, dados no payload, validade correta, sem mutação do dict original         |
| `tests/units/test_schemas.py`                | `TestUsuarioCreateSenhaForte` | Senha válida, sem maiúscula, sem minúscula, sem número, sem especial, muito curta, múltiplos erros |
| `tests/integrations/test_auth_routes.py`     | `TestAuthRoutes`              | `POST /auth/refresh` sucesso, token inválido, token revogado; logout com body correto              |

---

## 3. Estado atual do banco de dados (SQLite)

**Tabelas existentes:**

| Tabela                  | Descrição                                                         |
| ----------------------- | ----------------------------------------------------------------- |
| `clinica`               | Clínicas cadastradas                                              |
| `clinica_funcionamento` | Horários de funcionamento por dia da semana                       |
| `usuario`               | Usuários do sistema com `password_hash`, `role`, `clinica_id`     |
| `refresh_tokens`        | Tokens de renovação de sessão — **criada nesta sessão**           |
| `veterinario`           | Veterinários vinculados às clínicas                               |
| `integracao`            | Configurações de integração (Google Calendar, WhatsApp, Telegram) |
| `agendamento`           | Agendamentos de consultas                                         |

**Para recriar o banco:**

```bash
python src/yumi/database/init_db.py
```

---

## 4. Endpoints de autenticação (estado atual)

| Método | Rota                   | Autenticado | Descrição                                                                                    |
| ------ | ---------------------- | ----------- | -------------------------------------------------------------------------------------------- |
| POST   | `/api/v1/auth/login`   | Não         | Login — retorna `access_token`, `refresh_token` e dados do usuário. Limite: 5 req/min por IP |
| POST   | `/api/v1/auth/refresh` | Não         | Renova tokens via refresh token (rotação: token antigo é revogado)                           |
| POST   | `/api/v1/auth/logout`  | Não\*       | Revoga o refresh token no banco                                                              |
| GET    | `/api/v1/auth/me`      | Sim         | Retorna dados do usuário autenticado                                                         |

\*O logout recebe o `refresh_token` no body — não precisa do `Authorization` header.

---

## 5. Pendência registrada no README

**Token Blocklist no Logout (requer Redis)**

O `access_token` continua válido após logout pelo tempo de expiração (30min). Para invalidar completamente:

- Adicionar `jti` (UUID) no payload do `access_token`
- Criar `src/yumi/auth/token_blocklist.py`
- No logout: salvar `jti` na blocklist
- Em `dependencies.py`: verificar `jti` a cada requisição

**Armazenamento:** Redis em produção (`poetry add redis`). Em desenvolvimento, pode usar `set` Python (perde ao reiniciar).

---

## 6. Dependências relevantes do pyproject.toml

```toml
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]   # JWT
passlib[bcrypt]              # hash de senha
python-multipart             # OAuth2PasswordRequestForm
slowapi                      # rate limiting — adicionado nesta sessão
```

---

## 7. Próximos passos sugeridos

- Implementar a **token blocklist** com Redis (último item de segurança pendente)
- Evoluir o banco para **PostgreSQL** (o código já está preparado via SQLAlchemy — só mudar `DATABASE_URL`)
- Quando migrar para Postgres: substituir `init_db.py` + `models.sql` por **Alembic** (migrations)
- Adicionar **paginação** nas listagens (veterinários, agendamentos, usuários)
- Implementar lógica de **agendamento inteligente** (verificação de conflitos de horário)
