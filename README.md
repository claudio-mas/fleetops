# FleetOps

SaaS B2B de gestão de manutenção de frota e equipamentos.

> Migração técnica do sistema legado em Microsoft Access (`ERD.accdb`) para uma plataforma web multi-tenant moderna.
> Documento de requisitos completo: [PRD](docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md).

## Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16
- **Frontend**: React 18 + Vite + TypeScript + TailwindCSS
- **Infra dev**: Docker Compose (postgres + redis + api + frontend)
- **Pacotes**: `uv` (Python), `npm` (Node)

## Pré-requisitos

- Docker Desktop ≥ 4.x (com Docker Compose v2)
- `uv` ≥ 0.5 — `irm https://astral.sh/uv/install.ps1 | iex` (Windows) ou `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Node.js ≥ 20 (recomendado via `nvm`)
- Git ≥ 2.40

## Setup inicial

```powershell
# 1. Clonar o repositório
git clone <repo-url> Access
cd Access

# 2. Copiar variáveis de ambiente
Copy-Item .env.example .env
# Editar .env e trocar SECRET_KEY por uma string aleatória

# 3. Subir infra de dependências (postgres + redis)
docker compose up -d postgres redis

# 4. Instalar deps do backend
cd backend
uv sync
uv run alembic upgrade head
cd ..

# 5. Instalar deps do frontend
cd frontend
npm install
cd ..
```

## Workflow diário

### Subir tudo via Docker

```bash
docker compose up -d
# api → http://localhost:8000
# frontend (build de produção) → http://localhost:8080
# docs API → http://localhost:8000/docs
```

### Modo desenvolvimento (hot reload no frontend)

```bash
# Terminal 1: backend + deps em containers
docker compose up -d postgres redis api

# Terminal 2: frontend em dev mode (hot reload)
cd frontend
npm run dev
# → http://localhost:5173 (proxy /api → backend)
```

### Modo desenvolvimento full local (sem container do backend)

```bash
# Terminal 1: dependências
docker compose up -d postgres redis

# Terminal 2: backend em dev mode
cd backend
$env:DATABASE_URL="postgresql+asyncpg://fleetops:fleetops_dev_password@localhost:5433/fleetops"
$env:REDIS_URL="redis://localhost:6379/0"
$env:SECRET_KEY="any-local-secret-32-chars-or-more"
$env:ENVIRONMENT="dev"
uv run fastapi dev app/main.py --port 8000

# Terminal 3: frontend
cd frontend
npm run dev
```

> **Nota:** a porta local do Postgres é `5433` (se `5432` já estiver em uso, ajuste `POSTGRES_PORT` no `.env`).

## Testes

```bash
# Backend
cd backend
uv run pytest -v

# Frontend
cd frontend
npm test

# Tudo (requer make)
make test
```

## Lint e formatação

```bash
# Backend
cd backend
uv run ruff check .
uv run ruff format .
uv run mypy app

# Frontend
cd frontend
npm run lint
npm run format
```

## Migrations (Alembic)

```bash
# Aplicar todas pendentes
docker compose exec api alembic upgrade head
# ou: cd backend && uv run alembic upgrade head

# Criar nova migration (P1+ depois que houver modelos)
docker compose exec api alembic revision --autogenerate -m "descrição"

# Voltar uma versão
docker compose exec api alembic downgrade -1
```

## Estrutura do repo

```
backend/        # FastAPI app, models, alembic, tests
frontend/       # React app, components, tests
docker-compose.yml
.github/workflows/ci.yml
docs/superpowers/
  specs/        # PRDs (design specs)
  plans/        # Implementation plans
.env.example
Makefile
```

## Documentos

### Especificações
- [PRD Completo — Migração Access → SaaS](docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md)

### Planos de Implementação
- [P0 — Foundation & Dev Environment](docs/superpowers/plans/2026-05-15-p0-foundation-dev-environment.md) ✅ **Concluído**
- [P1 — Multi-tenant Auth & RBAC](docs/superpowers/plans/2026-05-22-p1-multitenant-auth-rbac.md) ✅ **Concluído**
- [P2 — Email Verification, User Invitation & MFA](docs/superpowers/plans/2026-05-26-p2-email-verification-user-invitation-mfa.md) ✅ **Concluído**
- [P4 — Cadastros Básicos](docs/superpowers/plans/2026-06-03-p4-cadastros-basicos.md) ✅ **Concluído**

### Guias Técnicos
- [P2 Comprehensive Guide — Arquitetura, API, Security](docs/superpowers/P2_EMAIL_MFA.md)
- [Backend README — Setup, Testing, Deployment](backend/README.md)

## Próximos passos

### Status Atual
- ✅ **P0** — Foundation & Dev Environment (concluído)
- ✅ **P1** — Multi-tenant Auth & RBAC (concluído — 31 testes backend + 3 frontend)
- ✅ **P2** — Email Verification, User Invitation & MFA (concluído — 65 testes, 3,500+ linhas de código)
- ✅ **P4** — Cadastros Básicos (11 CRUDs full-stack com RLS, soft delete, optimistic lock)

### P3 Planejado
**Próximas fases** (não iniciadas):

1. **MFA Improvements** — Backup codes, SMS OTP, WebAuthn/FIDO2
2. **SSO Integration** — Google, Microsoft, GitHub OAuth
3. **Email Templates** — Customização por tenant, branding
4. **Webhook Delivery** — Rastreamento de status de envio via Resend
5. **Bulk User Import** — CSV upload com fluxo de invitação automática
6. **Advanced RBAC** — Permissões customizáveis por tenant
7. **Audit Trail** — Log imutável de todas as ações

Ver [PRD](docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md) para roadmap completo e priorização.
