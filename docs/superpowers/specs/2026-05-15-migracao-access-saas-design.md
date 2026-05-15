# PRD — Migração do Sistema Access para SaaS B2B

**Projeto**: Modernização do sistema legado de Gestão de Manutenção de Frota/Equipamentos (Microsoft Access) para uma plataforma SaaS B2B multi-tenant baseada em Python/FastAPI + React + PostgreSQL.

| Campo | Valor |
|---|---|
| **Versão** | 1.0 |
| **Data** | 2026-05-15 |
| **Status** | Aprovado para fase de planejamento técnico |
| **Tipo de documento** | Product Requirements Document (PRD) |
| **Origem** | Sessão de brainstorming a partir do levantamento do `ERD.accdb` (23 tabelas, 46 formulários, 33 relatórios, 10 módulos VBA) |
| **Próximo passo** | Detalhamento de plano de implementação (writing-plans) |

---

## Sumário

1. [Visão geral e proposta de valor](#1-visão-geral-e-proposta-de-valor)
2. [Arquitetura técnica](#2-arquitetura-técnica)
3. [Modelo de dados](#3-modelo-de-dados)
4. [Módulos funcionais do MVP](#4-módulos-funcionais-do-mvp)
5. [Fluxos críticos](#5-fluxos-críticos)
6. [Requisitos não-funcionais, segurança e compliance](#6-requisitos-não-funcionais-segurança-e-compliance)
7. [Roadmap pós-MVP e KPIs](#7-roadmap-pós-mvp-e-kpis)
8. [Glossário](#8-glossário)
9. [Registro de decisões](#9-registro-de-decisões)
10. [Itens em aberto / TBD](#10-itens-em-aberto--tbd)

---

## 1. Visão geral e proposta de valor

### 1.1 Produto

**FleetOps SaaS** (nome de trabalho — definitivo a ser definido na fase comercial) — plataforma web/PWA de gestão de manutenção de frota e equipamentos em modelo SaaS B2B self-service, voltada a empresas brasileiras pequenas e médias.

### 1.2 Proposta de valor

- **Pronto em minutos**: signup → trial 7 dias sem cartão → cliente começa imediatamente.
- **Operacional no campo**: operadores e mecânicos registram abastecimentos, atividades e ordens de serviço pelo celular (PWA com câmera nativa).
- **Visibilidade em tempo real**: dashboards de custo por equipamento, próximas manutenções e OS pendentes.
- **Compliance fiscal e legal**: NFe automática via Asaas, audit log completo, LGPD-friendly.
- **Preço justo**: modelo híbrido tier + consumo, começa em R$ 99/mês.

### 1.3 Público-alvo

- Empresas brasileiras pequenas e médias com 10–500 equipamentos.
- Segmentos: locadoras de veículos, frotas urbanas, agronegócio, mineração leve, indústria com máquinas críticas, construção civil.
- Perfil atual: usam Excel, Access caseiro, ERP genérico inadequado ou software caro (Trackmob, Cigam Fleet, Volpe).
- Valor central buscado: autonomia (self-service, sem implantação demorada).

### 1.4 Modelo de monetização

Híbrido **tier + consumo**, com 4 planos pagos + trial. Billing 100% via Asaas (PIX, boleto, cartão, NFe automática).

| Plano | Preço/mês | Usuários | Equipamentos | Recursos principais |
|---|---|---|---|---|
| **Trial** | Grátis 7 dias | 3 | 10 | Todos os recursos do Pro |
| **Starter** | R$ 99 | até 3 | até 20 | Cadastros + Abastecimento + Atividade |
| **Pro** | R$ 299 | até 15 | até 100 | Tudo + Manutenção + OS + Planos + Relatórios |
| **Business** | R$ 699 | até 50 | até 500 | Tudo + API + dashboards avançados + audit |
| **Enterprise** | Sob consulta | ilimitado | ilimitado | Tudo + SLA + onboarding dedicado |

Trial **sem cartão**. Conversão exige cadastrar forma de pagamento. Tabela é ponto de partida; ajustes finos virão da fase comercial.

---

## 2. Arquitetura técnica

### 2.1 Stack consolidada

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 async + Alembic | Async nativo, validação Pydantic, OpenAPI automático |
| Auth | FastAPI Users + Argon2id + JWT | Multi-tenant aware, MFA via TOTP |
| Frontend | React 18 + Vite + TypeScript + TanStack Query + Zustand | Stack moderna, type-safety end-to-end |
| UI | TailwindCSS + shadcn/ui + React Hook Form + Zod | Customizável (white-label leve), validação compartilhada |
| DB | PostgreSQL 16 | RLS nativo para multi-tenant |
| Cache + fila | Redis 7 | Sessões, rate limit, fila de tasks |
| Async | Celery + Redis broker | E-mails, PDFs, WhatsApp, NFe, alertas agendados |
| PWA | Vite PWA plugin + Workbox | Service worker, manifest, offline básico |
| PDF | WeasyPrint | HTML/CSS → PDF, customizável por tenant |
| Container | Docker + Docker Compose | Padrão de mercado |
| Reverse proxy | Caddy 2 | TLS automático Let's Encrypt |
| Object storage | S3-compatível (Backblaze B2 ou Wasabi) | Anexos, PDFs gerados, backups; custo baixo |
| Observability | Sentry + Uptime Kuma + Loki/Grafana (opcional) | Stack leve para VPS |
| CI/CD | GitHub Actions → deploy SSH/Ansible | Sem orquestrador caro |

### 2.2 Estratégia de tenancy

**Decisão**: Row-Level Security (RLS) com schema compartilhado.

- 1 database, 1 schema, todas as tabelas operacionais com coluna `tenant_id`.
- Políticas RLS no PostgreSQL filtram automaticamente por `tenant_id` usando `SET LOCAL app.current_tenant`.
- Backend define o `tenant_id` na sessão a cada request (extraído do JWT).
- **Defense in depth**: além da RLS, decorator do FastAPI valida tenant_id no payload.

**Critérios para migrar para outro modelo** no futuro:
- Schema-per-tenant: se ultrapassar 100+ tenants Enterprise com requisitos de isolamento.
- DB-per-tenant: apenas para clientes Enterprise específicos com SLA estrito e exigência contratual.

### 2.3 Topologia de deploy (MVP)

```
┌────────────────────────────────────────────────────┐
│  VPS (4 vCPU / 8GB RAM)                            │
│  ┌──────────────────────────────────────────────┐  │
│  │  Caddy (TLS, reverse proxy, gzip)            │  │
│  └─────┬───────────────────┬────────────────────┘  │
│        │                   │                       │
│  ┌─────▼──────┐    ┌──────▼─────────┐              │
│  │  React SPA │    │  FastAPI       │              │
│  │  (static)  │    │  (uvicorn)     │              │
│  └────────────┘    └──┬──────────┬──┘              │
│                       │          │                 │
│                  ┌────▼─────┐ ┌──▼──────┐          │
│                  │ Postgres │ │  Redis  │          │
│                  │  16      │ │   7     │          │
│                  └──────────┘ └────┬────┘          │
│                                    │               │
│                       ┌────────────▼─────┐         │
│                       │  Celery worker   │         │
│                       │  Celery beat     │         │
│                       └──────────────────┘         │
└─────────────┬──────────────────────────────────────┘
              │
              ▼
   ┌─────────────────────┐
   │  S3-compatível      │
   │  (Backblaze B2)     │
   │  - Anexos           │
   │  - Backups          │
   └─────────────────────┘
```

### 2.4 Backups e DR

- `pg_dump` diário → S3 (retenção 30 dias).
- WAL archiving contínuo → S3 (point-in-time recovery janela 7 dias).
- Restore test automatizado semanal em VPS espelho.
- Anexos: S3 com versionamento de objetos.

### 2.5 Gatilhos de escalonamento

| Métrica | Gatilho | Ação |
|---|---|---|
| Tenants pagantes | 30 | Migrar Postgres para gerenciado (Neon ou Cloud SQL) |
| MRR | R$ 15.000 | Worker Celery em VPS dedicada |
| MRR | R$ 30.000 | Migrar app para cloud gerenciada com auto-scaling |
| Latência p95 sustentada | > 800ms | Investigar e escalar antecipadamente |

### 2.6 Trade-offs aceitos da escolha "VPS puro"

A escolha explícita do usuário foi VPS puro, com aceitação de:

- Equipe assume responsabilidade integral por patches, backups, replicação, monitoramento e HA.
- Mitigações obrigatórias: backup off-site contínuo, monitoramento ativo, runbook de restore testado mensalmente, hardening padrão Linux, certificado TLS automatizado, fail2ban, firewall.
- Plano de saída registrado: ao atingir gatilhos de escala, migrar para cloud gerenciada.

---

## 3. Modelo de dados

### 3.1 Visão por domínios

```
┌────────────────────────────────────────────────────────────────────┐
│  DOMÍNIO SAAS (NOVO)                                               │
│  • tenant, tenant_setting                                          │
│  • user, role, user_role (RBAC)                                    │
│  • plan, plan_limit                                                │
│  • subscription, invoice                                           │
│  • usage_meter                                                     │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  DOMÍNIO CADASTROS / CATÁLOGOS                                     │
│  • centro_custo, conta_contabil                                    │
│  • cargo, colaborador                                              │
│  • fornecedor                                                      │
│  • combustivel                                                     │
│  • tipo_equipamento, tipo_servico                                  │
│  • grupo_insumo, insumo, unidade_medida                            │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  DOMÍNIO EQUIPAMENTOS (núcleo do produto)                          │
│  • equipamento (horímetro, km, foto, QR, centro de custo)          │
│  • equipamento_plano (planos de manutenção preventiva)             │
│  • equipamento_checklist (itens de verificação periódica)          │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  DOMÍNIO TRANSACIONAL                                              │
│  • abastecimento                                                   │
│  • atividade                                                       │
│  • manutencao + manutencao_item                                    │
│  • ordem_servico + ordem_servico_item                              │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  DOMÍNIO INFRA (NOVO — cross-cutting)                              │
│  • audit_log (particionado por mês)                                │
│  • attachment                                                      │
│  • notification                                                    │
│  • import_job                                                      │
│  • outbox_event (transactional outbox para Asaas)                  │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Mapeamento Access → SaaS

| Access (origem) | SaaS (destino) | Observação |
|---|---|---|
| `tbl_*` (23 tabelas) | tabelas no domínio correspondente | Nomes sem prefixo |
| `cod_*` (PK INTEGER) | `id` UUID v7 | Ordenação temporal + segurança |
| `id_*` (FK) | `*_id` UUID | Padrão moderno |
| `usuarios` | `user` + `tenant` + `user_role` | RBAC dedicado |
| `tblImagensRibbons`, `USysRibbons` | descartado | Sem paralelo na web |
| `tbls_*` (filhas) | `*_item` | Convenção mais legível |
| `tbl_parametros` | `tenant_setting` | Config por tenant |

### 3.3 Padrão de toda tabela operacional

```sql
id              UUID v7 PRIMARY KEY
tenant_id       UUID NOT NULL REFERENCES tenant(id)
created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
created_by      UUID REFERENCES "user"(id)
updated_by      UUID REFERENCES "user"(id)
deleted_at      TIMESTAMPTZ NULL  -- soft delete
version         INT NOT NULL DEFAULT 1  -- optimistic locking

-- Política RLS automática:
CREATE POLICY tenant_isolation ON <tabela>
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Índices padrão:
CREATE INDEX ON <tabela> (tenant_id);
CREATE INDEX ON <tabela> (tenant_id, created_at DESC);
```

### 3.4 Decisões de modelagem

| Decisão | Escolha | Razão |
|---|---|---|
| PK | UUID v7 | Ordenação temporal + sem enumeração entre tenants |
| Soft delete | `deleted_at` nullable | Audit + LGPD |
| Optimistic locking | coluna `version` | Conflitos de edição concorrente |
| Unicidade | sempre composta com `tenant_id` | Ex.: `UNIQUE(tenant_id, codigo_equipamento)` |
| Timezone | `TIMESTAMPTZ` em tudo | Suporte a múltiplos fusos no futuro |
| Dinheiro | `NUMERIC(15,4)` | Nunca FLOAT |
| Audit log | tabela separada particionada por mês | Performance + retenção configurável |
| Anexos | metadados no DB, blob no S3 | DB menor, backup mais barato |

### 3.5 Modernizações vs Access

- Identificadores: códigos sequenciais → UUID v7.
- Soft delete: agora padrão.
- Auditoria: `created_by` e `updated_by` em todas as entidades.
- Concorrência: locking otimista (Access era single-user efetivo).
- Modularidade: cabeçalho e item separados em manutenção e OS.
- Anexos: novo recurso (fotos, NF, PDFs).
- Notificações: novo recurso (fila persistente de avisos).

### 3.6 Estimativa de volume (tenant Plano Pro, 50 equipamentos)

| Entidade | Registros/ano | 5 anos |
|---|---|---|
| abastecimento | ~3.000 | 15.000 |
| atividade | ~12.000 | 60.000 |
| manutencao + itens | ~500 + 2.000 | 12.500 |
| ordem_servico | ~600 | 3.000 |
| audit_log | ~50.000 | 250.000 (particionado) |

Total: ~350k registros em 5 anos por tenant → Postgres confortável em VPS dimensionada.

---

## 4. Módulos funcionais do MVP

### 4.1 Bloco SaaS Infra (novos)

| ID | Módulo | Descrição | MVP |
|---|---|---|---|
| S1 | Onboarding & Tenant Signup | Landing → cadastro (CNPJ + razão social) → cria tenant, primeiro Admin, trial 7d, verificação de e-mail | ✅ |
| S2 | Billing & Assinaturas | Catálogo de planos → checkout Asaas (PIX/boleto/cartão) → ciclo de vida → webhooks → NFe automática | ✅ |
| S3 | Gestão de Usuários & RBAC | Convite por e-mail, papéis Admin/Gestor/Operador/Mecânico/Leitura, MFA TOTP opcional | ✅ |
| S4 | Tenant Settings | Logo, cores primárias, fuso horário, formato fiscal, política de senhas, política de MFA | ✅ |
| S5 | Plano de uso e limites | Consumo vs limite, alertas "80%", upsell automático | ✅ |

### 4.2 Bloco Operacional (réplica modernizada do Access)

| ID | Módulo | Modernização aplicada | MVP |
|---|---|---|---|
| O1 | Cadastros básicos | CRUDs padronizados, busca, paginação, soft delete, importação CSV | ✅ |
| O2 | Colaboradores | Vínculo opcional com `user` do sistema | ✅ |
| O3 | Equipamentos | Foto, anexos, QR code, histórico unificado em uma tela | ✅ |
| O4 | Planos de Manutenção | Triggers por horímetro/km/data, alertas WhatsApp/e-mail | ✅ |
| O5 | Abastecimento | Foto da bomba/NF via PWA, geolocalização opcional, consumo médio automático | ✅ |
| O6 | Atividade (horímetro) | Apontamento rápido pelo PWA do operador, foto do painel | ✅ |
| O7 | Ordens de Serviço | State machine (Aberta → Em execução → Aguard. peça → Concluída → Cancelada), anexos, comentários | ✅ |
| O8 | Manutenção | Vínculo com plano (fecha o "previsto"), insumos consumidos | ✅ |
| O9 | Histórico unificado | Timeline visual, filtros por tipo, export PDF/CSV | ✅ |

### 4.3 Bloco Visibilidade (modernização)

| ID | Módulo | Descrição | MVP |
|---|---|---|---|
| V1 | Dashboard executivo | Equipamentos ativos, custo do mês, consumo médio, OS abertas, próximas manutenções | ✅ |
| V2 | Dashboard operacional | OS atrasadas, manutenções vencidas, equipamentos parados | ✅ |
| V3 | Relatórios PDF essenciais | 10–15 via WeasyPrint (1 versão por entidade) | ✅ |
| V4 | Exportação CSV/Excel | Em qualquer listagem paginada | ✅ |

### 4.4 Bloco Suporte (utilitários)

| ID | Módulo | Descrição | MVP |
|---|---|---|---|
| U1 | Importação por planilha | Wizard genérico com dry-run | ✅ |
| U2 | Notificações | Central in-app + e-mail + WhatsApp | ✅ |
| U3 | Audit log viewer | Filtros por usuário/ação/entidade/período | ✅ |
| U4 | Anexos | Upload S3, vinculados a entidades | ✅ |
| U5 | Central de ajuda | FAQ, vídeos, atalho de suporte | ✅ |
| U6 | Feedback in-app | Botão persistente | ✅ |

### 4.5 Matriz de feature gating

| Feature | Starter | Pro | Business | Enterprise |
|---|:---:|:---:|:---:|:---:|
| Cadastros + Equipamentos | ✅ | ✅ | ✅ | ✅ |
| Abastecimento + Atividade | ✅ | ✅ | ✅ | ✅ |
| Manutenção + OS | — | ✅ | ✅ | ✅ |
| Planos de manutenção | — | ✅ | ✅ | ✅ |
| Relatórios PDF | 3 | 10–15 | 10–15 | 10–15 |
| Dashboards | Básico | ✅ | Avançado | Avançado |
| WhatsApp alertas | — | ✅ | ✅ | ✅ |
| Importação por planilha | ✅ | ✅ | ✅ | ✅ |
| Audit log viewer | — | — | ✅ | ✅ |
| API REST (v2) | — | — | ✅ | ✅ |
| SLA contratual | — | — | — | ✅ |
| Onboarding dedicado | — | — | — | ✅ |

### 4.6 Fora do MVP (referência rápida)

- App híbrido React Native (v2).
- Login social Google e Microsoft (v2).
- API REST pública + webhooks de saída (v2).
- Telemetria/IoT (v3).
- Multi-idioma (sob demanda).
- Integrações ERP específicas (sob demanda Enterprise).

---

## 5. Fluxos críticos

### 5.1 Signup → Trial → Conversão

- Landing → form com nome, e-mail, CNPJ, razão social, senha.
- Cria tenant em status `trial` com `expires_at = now + 7d`, plano Pro virtual.
- Cria primeiro `user` como Owner; envia e-mail de verificação.
- Após verificação → onboarding wizard 4 passos (logo, equipe, primeiro equipamento, tour).
- Durante trial: banner persistente com contagem, e-mails de engagement (dia 3, 5, 6).
- Conversão: forma de pagamento → Asaas → status `aguard_pagto` → `ativa`.
- Não-conversão: status `expirado`, acesso bloqueado exceto upgrade, retenção 30 dias, e-mails de win-back.

**Regras**:
- Apenas 1 trial por CNPJ (verificação adicional por IP e e-mail).
- Trial não cobra cartão; ao converter, registra forma de pagamento.
- Após 30 dias de expirado, dados anonimizados (LGPD); emissão fiscal retida 5 anos.

### 5.2 Billing (ciclo de vida da assinatura)

```
        ┌──────────┐
        │  trial   │  ──[7 dias]──►  expirado
        └────┬─────┘
             │ upgrade
             ▼
        ┌──────────┐                  ┌──────────────┐
        │ aguard.  │ ◄────────────── │  inadimplente │
        │ pagto    │                  └──────┬────────┘
        └────┬─────┘                         ▲
             │ PAYMENT_RECEIVED               │
             ▼                                │
        ┌──────────┐    [vencido 3d]          │
        │  ativa   │ ──────────────────────►──┘
        └────┬─────┘                          │ [vencido 15d]
             │ user cancela                    ▼
             ▼                          ┌──────────────┐
        ┌──────────┐                    │   suspensa   │
        │ cancelada│ ◄────────────────  │  (bloqueada) │
        └──────────┘                    └──────────────┘
```

**Efeitos por estado**:

| Estado | Acesso app | Acesso dados | Cobrança |
|---|---|---|---|
| trial | total (limites Pro) | total | nenhuma |
| aguardando_pagto | total | total | 1ª cobrança gerada |
| ativa | total | total | recorrente |
| inadimplente | total com banner | total | retry |
| suspensa | bloqueado | leitura | encerrada |
| cancelada | bloqueado | export + exclusão | encerrada |
| expirado | bloqueado (upgrade) | bloqueado | nunca houve |

**Webhook Asaas (idempotente)**:
- Eventos: `PAYMENT_CREATED`, `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_REFUNDED`, `SUBSCRIPTION_*`, `INVOICE_*`.
- Registra em `asaas_event_log` com idempotency key = `event_id`.
- Processamento assíncrono via Celery, retry exponencial até 24h, depois alerta interno.
- Resposta HTTP 200 imediata; processamento desacoplado.
- Reconciliação diária via cron para detectar eventos perdidos.

### 5.3 Plano de Manutenção e Alertas

- Plano define gatilho (HORIMETRO / KM / DATA), frequência, tipo de serviço, alerta antecipado (default 80%), insumos previstos.
- Celery beat roda a cada 1h: para cada plano ativo, calcula "% até próximo serviço" usando última leitura de horímetro/km/data; ≥ 80% e ainda não notificado → cria `notification`.
- Tela "Próximas manutenções" lista por urgência com status verde / amarelo / vermelho; botão "Abrir OS deste plano" pré-preenche.
- OS concluída e vinculada → ciclo do plano fechado, contador reinicia.

**Regras**:
- Notificação para o mesmo plano não repete em < 24h.
- WhatsApp dispara apenas para `Gestor` e `Admin`; operadores recebem in-app.
- Equipamento sem leitura há > 30 dias → plano em pausa, alerta de "sem leitura" para gestor.

### 5.4 Importação por planilha

- Passo 1: escolhe entidade alvo, baixa template Excel.
- Passo 2: upload do arquivo preenchido.
- Passo 3: mapeamento de colunas (sugestão automática por similaridade).
- Passo 4: dry-run com validação completa — mostra X válidas, Y com erros detalhados por linha.
- Passo 5: confirmação → job assíncrono (Celery) com progresso em tempo real → e-mail ao concluir com relatório.

**Regras**:
- Limite MVP: 10.000 linhas por importação.
- Transação por chunk de 500 linhas (falha parcial não corrompe).
- Histórico persistido em `import_job`.
- Validação respeita unicidade composta por tenant.

### 5.5 Ordem de Serviço (state machine)

```
        ┌──────────┐
        │  ABERTA  │
        └────┬─────┘
             │ atribui mecânico + começa
             ▼
        ┌─────────────────┐
        │  EM EXECUÇÃO    │◄────────┐
        └────┬────────┬───┘         │ peça chegou
             │        │ falta peça  │
             │        ▼             │
             │   ┌──────────────────┴┐
             │   │ AGUARDANDO PEÇA   │
             │   └───────────────────┘
             │ finaliza
             ▼
        ┌──────────────┐
        │  CONCLUÍDA   │  (imutável)
        └──────────────┘

        (em qualquer estado exceto CONCLUÍDA)
                ↓
        ┌──────────────┐
        │  CANCELADA   │  (motivo obrigatório)
        └──────────────┘
```

**Regras**:
- Mudança de estado registra em `audit_log` com usuário, timestamp e motivo.
- OS concluída não pode ser editada — só duplicada para correção.
- OS aberta > 7 dias dispara notificação para gestor.

---

## 6. Requisitos não-funcionais, segurança e compliance

### 6.1 Segurança da aplicação

| Categoria | Requisito |
|---|---|
| Transporte | TLS 1.3 obrigatório (Caddy + Let's Encrypt) |
| Autenticação | Argon2id |
| Política de senha | Mínimo 10 caracteres + complexidade; tenant pode endurecer |
| Sessões | JWT 15min + refresh token 7d rotativo |
| MFA | TOTP opcional; obrigatório por config do tenant |
| Rate limiting | 100 req/min público; 1000/min autenticado (slowapi + Redis) |
| CSRF | Tokens em rotas mutativas |
| CORS | Whitelist explícita; domínio personalizado em planos altos |
| Isolamento | RLS Postgres + decorator backend (defense in depth) |
| Injection | SQLAlchemy ORM + Pydantic |
| XSS | React escapa por padrão; lint contra `dangerouslySetInnerHTML` |
| Segredos | Variáveis de ambiente, nunca no repositório |
| Headers | CSP estrita, HSTS, X-Frame-Options, X-Content-Type-Options |
| Upload | Validação MIME real (python-magic), tamanho máx, URLs S3 assinadas |
| Logs sensíveis | Mascaramento de PII antes de log |
| Pentest | Antes do lançamento comercial e anual |

### 6.2 LGPD — implementação operacional (decisão C1)

| Direito do titular | Como atender |
|---|---|
| Acesso | Export do colaborador via tela (PDF/JSON) |
| Correção | CRUD de Colaborador |
| Exclusão | Soft delete + anonimização (nome, e-mail, CPF) preservando dados operacionais sem PII |
| Portabilidade | Export estruturado JSON |
| Oposição/Limitação | Manual via DPO da contratante |
| Revogação de consentimento | Cancelamento → 30d → anonimização global; fiscal retido 5 anos |

**Documentação obrigatória pública**:
- Política de Privacidade
- Termos de Uso
- DPA (Data Processing Agreement) anexável a contratos Enterprise
- Política de cookies (banner)

**Subcontratados (operadores) declarados publicamente**:
- Asaas (pagamentos + NFe)
- VPS provider
- Backblaze B2 / Wasabi (armazenamento)
- Provedor de WhatsApp (Twilio / Z-API / WhatsApp Cloud API)
- Provedor de e-mail (SendGrid / Resend / SES)
- Sentry (configurado para não capturar PII)

### 6.3 Audit log (decisão B1)

| Aspecto | Especificação |
|---|---|
| Eventos | CREATE/UPDATE/DELETE em todas as entidades operacionais + autenticação + ações administrativas |
| Estrutura | `id, tenant_id, user_id, ip, user_agent, ação, entidade, entidade_id, diff_before (JSONB), diff_after (JSONB), timestamp` |
| Imutabilidade | Tabela sem UPDATE/DELETE permitidos; apenas INSERT |
| Retenção | 24 meses online + arquivamento S3 até 5 anos |
| Particionamento | Mensal (declaração nativa Postgres) |
| Acesso | Roles Admin e Auditor; pesquisa por filtros |
| Performance | Escrita assíncrona via fila |

### 6.4 Performance e capacidade

| Métrica | Alvo MVP |
|---|---|
| Latência API p50 | < 200ms |
| Latência API p95 | < 800ms |
| Latência API p99 | < 1.500ms |
| TTFB frontend | < 1s |
| LCP | < 2.5s |
| PDF até 500 linhas | < 5s (assíncrono se maior) |
| Importação 1.000 linhas | < 30s |
| Conexões WebSocket simultâneas | 500 |
| Pool Postgres | 20 por instância FastAPI |

**Capacidade VPS inicial** (4 vCPU / 8 GB RAM): ~30 tenants ativos, ~150 usuários online simultâneos.

**Gatilho de escala vertical**: CPU > 70% sustentado por 1h, ou RAM > 85%.

### 6.5 Disponibilidade, backup e DR

| Aspecto | Especificação MVP |
|---|---|
| Uptime alvo | 99,5% mensal (best-effort, sem SLA contratual) |
| Janela de manutenção | Domingo 02h–04h BRT, aviso 7 dias antes |
| Backup full | `pg_dump` diário → B2, retenção 30 dias |
| Backup contínuo | WAL archiving (PITR janela 7 dias) |
| Backup arquivos | B2 com versionamento de objetos |
| Restore test | Automatizado semanal em VPS espelho |
| RPO | 15 minutos |
| RTO | 4 horas |
| DR runbook | Documentado, testado a cada 6 meses |

### 6.6 Observability

| Camada | Ferramenta |
|---|---|
| Erros app | Sentry (free tier inicial) |
| Logs | Loki + Promtail (ou arquivo + logrotate no MVP mais simples) |
| Métricas infra | node_exporter + Prometheus + Grafana (opcional) |
| Healthchecks | Uptime Kuma self-hosted ou UptimeRobot free |
| Métricas de negócio | Tabela `usage_meter` + dashboard interno |
| Alertas | Uptime Kuma → Telegram/Discord/e-mail |

### 6.7 Suporte ao cliente

| Canal | Cobertura |
|---|---|
| E-mail | Todos os planos |
| WhatsApp | Pro e acima |
| Chat in-app (Crisp/Tawk) | Todos os planos |
| Help center | Todos os planos |
| SLA de resposta | Best-effort no MVP (1º contato 8h úteis; 4h para Business/Enterprise) |
| Onboarding dedicado | Apenas Enterprise |

### 6.8 Internacionalização

- MVP apenas pt-BR.
- Estrutura preparada (react-i18next no frontend, tabela de traduções no backend) para futuro expansão sem refactor pesado.
- Datas, números e moeda respeitando locale brasileiro.

---

## 7. Roadmap pós-MVP e KPIs

### 7.1 Roadmap v2 (6–12 meses após MVP)

| Prioridade | Iniciativa | Justificativa |
|---|---|---|
| 🔴 Alta | App híbrido React Native (Capacitor) | Operadores em campo, retenção |
| 🔴 Alta | API REST pública com API key | Diferencial Business+ |
| 🟡 Média | Login social Google/Microsoft | Reduz fricção signup |
| 🟡 Média | Webhooks de saída | Integrações BI/ERP dos clientes |
| 🟡 Média | Relatórios paramétricos | Reduz pedidos de customização |
| 🟢 Baixa | Multi-idioma estrutural | Expansão internacional |
| 🟢 Baixa | Campos customizados em entidades | Diferencial Enterprise |

### 7.2 Roadmap v3+ (12–24 meses)

- **Telemetria/IoT** (Suntech, Maxtrack, OBD-II): elimina apontamento manual, grande diferencial.
- **Mobile com offline robusto**: para áreas remotas (mineração, agro).
- **Marketplace de peças**: receita adicional via comissionamento.
- **BI embedado** (Metabase/Superset): plano Enterprise.
- **Machine Learning**: predição de falha, otimização de plano de manutenção.
- **DB-per-tenant** Enterprise sob SLA estrito.
- **Integrações ERP** (Sankhya, Totvs, SAP B1) sob demanda.
- **Apps nativos separados** (Swift/Kotlin) só se híbrido provar limitante.

### 7.3 KPIs de sucesso

**Produto** (mensal):

| KPI | Definição | Alvo Ano 1 |
|---|---|---|
| Conversão Trial → Pago | % de tenants em trial que viram assinatura | ≥ 15% |
| Activation rate | % de tenants que cadastram ≥ 5 equipamentos no trial | ≥ 50% |
| Time-to-first-value | Tempo do signup ao 1º abastecimento/atividade | < 24h |
| DAU/MAU | Engajamento | > 25% |
| Adoção PWA | % de operacionais que instalam PWA | > 40% |
| NPS | Promotores − detratores | > 30 (good); > 50 (excellent) |

**Negócio**:

| KPI | Definição | Alvo Ano 1 |
|---|---|---|
| MRR | Receita recorrente mensal | A definir após validação |
| Churn mensal | % de tenants pagantes que cancelam | < 5% |
| CAC | Custo de aquisição por cliente | < 3 meses de LTV |
| LTV/CAC | Razão | > 3x |
| ARPU | Receita média por tenant | tendência crescente |
| Net Revenue Retention | Receita de mesmo conjunto com upsells | ≥ 100% |

**Técnicos**: ver seção 6.4.

### 7.4 Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| VPS única = SPOF | Média | Alto | Backup off-site, DR runbook testado, gatilho de migração para cloud em R$30k MRR |
| Webhook Asaas perdido | Baixa | Alto | Idempotência por event_id + outbox + cron de reconciliação |
| Vazamento entre tenants (bug RLS) | Baixa | Crítico | RLS + decorator backend + test suite de isolamento |
| Importação corrompendo dados | Média | Alto | Dry-run obrigatório, transação por chunk, audit do import |
| Concorrência com players estabelecidos | Alta | Médio | UX moderna + preço SMB + onboarding self-service |
| LGPD enforcement em incidente | Baixa | Crítico | DPA, audit, anonimização, pentest anual |
| Asaas instabilidade ou mudança contratual | Baixa | Médio | Abstração da camada de billing — facilita troca |
| Equipe pequena sobrecarregada com infra VPS | Alta | Médio | Automação (Ansible, GitHub Actions), runbooks, contratar SRE quando MRR ≥ R$20k |

### 7.5 Definition of Launch (lançamento comercial público)

- [ ] Todos os módulos MVP em produção
- [ ] Pentest realizado e críticos resolvidos
- [ ] DR completo testado em < 4h
- [ ] 5 clientes piloto ativos por ≥ 30 dias sem incidentes graves
- [ ] Política de Privacidade, Termos e DPA revisados juridicamente
- [ ] NPS ≥ 30 com piloto
- [ ] Help center cobrindo ≥ 80% dos casos suportados
- [ ] Asaas em produção (não sandbox)
- [ ] SPF, DKIM, DMARC do domínio configurados
- [ ] Página de status pública (status.dominio.com)
- [ ] Backup restore validado ≥ 3 vezes seguidas

---

## 8. Glossário

| Termo | Definição |
|---|---|
| **Tenant** | Empresa cliente do SaaS; cada tenant tem dados isolados |
| **RLS** | Row-Level Security; mecanismo do Postgres que filtra linhas por política automática |
| **RBAC** | Role-Based Access Control; permissões definidas por papel atribuído ao usuário |
| **MRR** | Monthly Recurring Revenue; receita recorrente mensal somada de assinaturas ativas |
| **Churn** | Taxa de cancelamento de clientes pagantes |
| **ARPU** | Average Revenue Per User (na prática, por tenant) |
| **NPS** | Net Promoter Score (% promotores − % detratores) |
| **DAU/MAU** | Daily/Monthly Active Users; razão indica engajamento |
| **RPO** | Recovery Point Objective; quanto de dado pode ser perdido em desastre |
| **RTO** | Recovery Time Objective; tempo máximo para voltar ao ar |
| **PWA** | Progressive Web App; web instalável com capacidades nativas |
| **MFA / TOTP** | Multi-Factor Authentication / Time-based One-Time Password |
| **DPA** | Data Processing Agreement; contrato LGPD/GDPR entre controlador e operador |
| **DPO** | Data Protection Officer (Encarregado de Dados, na LGPD) |
| **PSP** | Payment Service Provider; Asaas é o PSP escolhido |
| **NFe** | Nota Fiscal Eletrônica |
| **PITR** | Point-In-Time Recovery; restaurar DB a um momento específico via WAL |
| **WAL** | Write-Ahead Log do Postgres; permite PITR |
| **SLA** | Service Level Agreement; compromisso contratual de disponibilidade |
| **SPOF** | Single Point Of Failure |
| **DR** | Disaster Recovery |

---

## 9. Registro de decisões

Decisões tomadas durante o brainstorming, em ordem cronológica:

| # | Decisão | Alternativas consideradas |
|---|---|---|
| D01 | Migração técnica do Access (manter funcionalidades, trocar tecnologia) | Modernização total, documentação, evolução em Access |
| D02 | Stack: Python FastAPI + React | .NET, Node.js, Java |
| D03 | Modelo: SaaS B2B self-service multi-tenant | Single tenant, B2B com onboarding manual, freemium |
| D04 | DB: PostgreSQL (mudou de SQL Server) | SQL Server, MySQL |
| D05 | Pagamento: Asaas (PIX/boleto/cartão + NFe) | Stripe, Iugu, Gerencianet |
| D06 | Escopo: réplica + modernizações essenciais para SaaS | Réplica fiel total, MVP enxuto, reimaginar produto |
| D07 | Pricing: híbrido tier + consumo, 4 planos + trial 7d sem cartão | Flat, tiered puro, por consumo puro, freemium |
| D08 | Mobile: PWA no MVP, app híbrido na v2 | Só web, app híbrido no MVP, apps nativos |
| D09 | Hosting: VPS puro (com plano de saída) | Cloud gerenciado, VPS + Postgres gerenciado, PaaS |
| D10 | Auth: própria com FastAPI Users | Auth0/Clerk, Keycloak, Supabase Auth |
| D11 | Login social Google na v2 | No MVP |
| D12 | MFA opcional no MVP | Sem MFA, MFA obrigatório, MFA por política do tenant |
| D13 | Audit log completo no MVP | Apenas auth e admin, sem audit |
| D14 | LGPD operacional manual (admin gerencia direitos via UI) | Fluxo formal DPO + portal de privacidade |
| D15 | Greenfield (sem migração de clientes Access existentes) | Migração de cliente âncora, múltiplos, wizard de import |
| D16 | Relatórios: híbrido (10–15 PDFs essenciais + dashboards + CSV) via WeasyPrint | Replicar todos, só dashboards, mecanismo genérico |
| D17 | Integrações MVP: e-mail + NFe Asaas + WhatsApp + importação CSV | Conjunto maior, conjunto menor, sem WhatsApp |
| D18 | Sem prazo — qualidade prioritária | Prazo agressivo 3-4m, equilibrado 4-6m, data fixa |
| D19 | Tenancy: RLS shared schema | Schema-per-tenant, DB-per-tenant |
| D20 | UI: TailwindCSS + shadcn/ui | Mantine, Chakra UI, Material UI |
| D21 | PDF: WeasyPrint | ReportLab, Playwright PDF |

---

## 10. Itens em aberto / TBD

Itens deliberadamente postergados para fases posteriores (planejamento técnico ou go-to-market):

| ID | Item | Quando decidir | Observação |
|---|---|---|---|
| T01 | Nome comercial definitivo do produto | Fase comercial / pré-launch | "FleetOps SaaS" é nome de trabalho |
| T02 | Domínio comercial | Fase comercial | Buscar com .com.br e .com disponíveis |
| T03 | Preços finais por plano | Após validação com piloto | Tabela atual é ponto de partida |
| T04 | Provedor VPS específico | Plano técnico | Candidatos: Hostinger BR, Hetzner com plano de migrar se exigência LGPD, Locaweb, KingHost |
| T05 | Provedor de e-mail transacional | Plano técnico | SendGrid / Resend / Amazon SES — escolher pelo melhor custo-benefício |
| T06 | Provedor WhatsApp | Plano técnico | Twilio / Z-API / WhatsApp Cloud API |
| T07 | Provedor S3-compatível | Plano técnico | Backblaze B2 (recomendado) ou Wasabi |
| T08 | Lista exata dos 10–15 relatórios PDF essenciais | Plano de implementação | Definir por curadoria a partir dos 33 do Access |
| T09 | Texto definitivo da Política de Privacidade, Termos e DPA | Pré-lançamento | Revisão jurídica obrigatória |
| T10 | Alvo MRR Ano 1 | Após primeiros 3 meses pós-lançamento | Depende de validação de canal de aquisição |
| T11 | Estratégia de marketing / canais de aquisição | Fora do escopo deste PRD | PRD separado de Go-to-Market |
| T12 | Identidade visual (logo, paleta) | Fase de design | Influencia onboarding wizard e PDF templates |

---

**Fim do documento.**
