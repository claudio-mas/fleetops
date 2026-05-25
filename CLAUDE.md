# OpenWolf

@.wolf/OPENWOLF.md

This project uses OpenWolf for context management. Read and follow .wolf/OPENWOLF.md every session. Check .wolf/cerebrum.md before generating code. Check .wolf/anatomy.md before reading files.


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto do projeto

**FleetOps SaaS** — migração de um sistema legado de gestão de manutenção de frota/equipamentos (Microsoft Access) para uma plataforma web multi-tenant (FastAPI + React + PostgreSQL).

O repositório está na fase de **pré-implementação (P0 não iniciado)**. O que existe hoje:

- `ERD.accdb` — banco Access original (23 tabelas, 46 formulários, 33 relatórios, 10 módulos VBA)
- `levantamento_access.py` — script de extração/análise do Access (ver abaixo)
- `vba_*/` — código VBA exportado em `.txt` por sessão de análise
- `levantamento_access_*.xlsx` — relatórios de levantamento gerados pelo script
- `docs/superpowers/specs/` — PRD completo (`2026-05-15-migracao-access-saas-design.md`)
- `docs/superpowers/plans/` — plano de implementação P0 (`2026-05-15-p0-foundation-dev-environment.md`)
- `.venv/` — virtualenv isolado **somente para o script de análise** (pyodbc, pandas, openpyxl, pywin32), não confundir com o futuro backend

A estrutura `backend/`, `frontend/`, `docker-compose.yml`, `Makefile` etc. ainda não existe — consulte o plano P0 antes de criar qualquer arquivo.

## Script de análise do Access

Extrai esquema, relacionamentos, queries, formulários, relatórios e VBA do `ERD.accdb`.

```powershell
# Ativar o virtualenv do script de análise (raiz do repo)
.venv\Scripts\Activate.ps1

# Executar extração completa (requer Microsoft Access instalado)
python levantamento_access.py "C:\Projeto\Access\ERD.accdb"

# Saídas geradas (ignoradas pelo git após P0):
#   levantamento_access_<TIMESTAMP>.xlsx
#   vba_<TIMESTAMP>/   (um .txt por módulo VBA)
```

## Comandos pós-P0 (quando o código existir)

```powershell
# Subir todos os serviços
docker compose up -d

# Backend — testes
cd backend; uv run pytest -v

# Backend — teste único
cd backend; uv run pytest tests/test_health.py -v

# Backend — lint + type check
cd backend; uv run ruff check .; uv run ruff format --check .; uv run mypy app

# Backend — formatação automática
cd backend; uv run ruff format .; uv run ruff check --fix .

# Frontend — testes
cd frontend; npm test

# Frontend — lint
cd frontend; npm run lint

# Migrations
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "descricao"

# Modo dev local (hot reload)
docker compose up -d postgres redis api   # Terminal 1
cd frontend; npm run dev                  # Terminal 2 → http://localhost:5173
```

## Arquitetura técnica

### Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 async · asyncpg · Alembic · uv |
| Auth | FastAPI Users · Argon2id · JWT (15min) + refresh (7d) |
| Frontend | React 18 · Vite · TypeScript · TanStack Query · Zustand |
| UI | TailwindCSS · shadcn/ui · React Hook Form · Zod |
| DB | PostgreSQL 16 (RLS para multi-tenant) |
| Cache/fila | Redis 7 · Celery |
| PDF | WeasyPrint |
| Dev | Docker Compose · Caddy (produção) |

### Monorepo

```
backend/        # FastAPI app, models, alembic migrations, pytest
frontend/       # React SPA, components, vitest
docker-compose.yml
Makefile
```

Frontend faz proxy de `/api` → backend durante dev (Vite). Em produção o nginx no container do frontend faz o mesmo.

### Multi-tenancy (RLS)

Todas as tabelas operacionais têm `tenant_id UUID NOT NULL`. O PostgreSQL aplica políticas RLS automaticamente com `SET LOCAL app.current_tenant`. O backend define o `tenant_id` na sessão a cada request (extraído do JWT) **e** valida via decorator FastAPI (defense in depth).

### Padrão de toda tabela operacional

```sql
id          UUID v7  PRIMARY KEY
tenant_id   UUID     NOT NULL  -- RLS aplicada aqui
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
created_by  UUID REFERENCES "user"(id)
updated_by  UUID REFERENCES "user"(id)
deleted_at  TIMESTAMPTZ NULL            -- soft delete
version     INT NOT NULL DEFAULT 1      -- optimistic locking
```

Unicidade sempre composta com `tenant_id` (ex.: `UNIQUE(tenant_id, codigo_equipamento)`). PKs são UUID v7 (nunca inteiros sequenciais). Valores monetários em `NUMERIC(15,4)`, nunca `FLOAT`. Todos os timestamps em `TIMESTAMPTZ`.

### Domínios do modelo de dados

```
SaaS Infra    → tenant, user, role, plan, subscription, invoice, usage_meter
Cadastros     → centro_custo, conta_contabil, cargo, colaborador, fornecedor,
                combustivel, tipo_equipamento, tipo_servico, grupo_insumo,
                insumo, unidade_medida
Equipamentos  → equipamento, equipamento_plano, equipamento_checklist
Transacional  → abastecimento, atividade, manutencao, manutencao_item,
                ordem_servico, ordem_servico_item
Infra cross   → audit_log (particionado por mês), attachment, notification,
                import_job, outbox_event
```

### Mapeamento Access → SaaS

- `tbl_*` → nome sem prefixo; `tbls_*` → `*_item`
- `cod_*` (PK INTEGER) → `id` UUID v7; `id_*` (FK) → `*_id` UUID
- `tbl_parametros` → `tenant_setting`
- `usuarios` → `user` + `tenant` + `user_role` (RBAC)
- `tblImagensRibbons`, `USysRibbons` → descartados

### Ordem de Serviço — state machine

`ABERTA → EM_EXECUÇÃO ↔ AGUARDANDO_PEÇA → CONCLUÍDA (imutável)`. Qualquer estado exceto CONCLUÍDA pode ir para `CANCELADA` (motivo obrigatório). Mudanças de estado registradas no `audit_log`.

## Decisões de design relevantes

- **Pacote manager backend**: `uv` (não pip nem poetry)
- **Lint Python**: ruff + mypy strict; line-length 100
- **UI**: shadcn/ui + TailwindCSS (não Mantine, Chakra, ou Material UI)
- **PDF**: WeasyPrint (não ReportLab nem Playwright)
- **Billing**: Asaas (PIX/boleto/cartão/NFe); abstração da camada facilita troca futura
- **Tenancy**: RLS shared schema (schema-per-tenant apenas se > 100 tenants Enterprise)
- **Mobile**: PWA no MVP; app híbrido (Capacitor) na v2
- **Login social**: apenas na v2
- **LGPD**: anonimização de dados pessoais após 30 dias de expirado; dados fiscais retidos 5 anos
- **Audit log**: imutável (só INSERT), particionado mensalmente, escrita assíncrona via fila

## Documentos de referência

- **PRD completo**: `docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md`
- **Plano P0**: `docs/superpowers/plans/2026-05-15-p0-foundation-dev-environment.md`
- **VBA original**: `vba_20260515_132158/` (versão mais completa das exportações)
