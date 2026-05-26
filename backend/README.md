# Backend — FleetOps SaaS

Python 3.12 · FastAPI · SQLAlchemy 2.0 async · asyncpg · PostgreSQL 16 · Celery · Redis

---

## Quick Start

### 1. Setup

```bash
# From project root
cd backend

# Create virtual environment (or use existing)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies via uv
uv pip install -r requirements.txt  # Or: uv sync

# Create .env from template
cp .env.example .env
```

### 2. Database

```bash
# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Run migrations
uv run alembic upgrade head

# (Optional) Seed data
uv run python scripts/seed.py
```

### 3. Run Backend

```bash
# Hot-reload development server
uv run fastapi dev app/main.py --port 8000

# Production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend runs at `http://localhost:8000`. API docs: `http://localhost:8000/docs`

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/fleet_ops
ALEMBIC_SQLALCHEMY_URL=postgresql://user:password@localhost/fleet_ops

# FastAPI
SECRET_KEY=your-secret-key-min-32-chars
API_PREFIX=/api/v1
ENVIRONMENT=development

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
EMAILS_FROM=noreply@yourdomain.com
EMAILS_FROM_NAME="FleetOps"

# MFA Settings
MFA_WINDOW=1  # Time window for TOTP validation (periods)

# Celery & Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Auth Token Lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## API Structure

### Authentication Endpoints (`/api/v1/auth`)
- `POST /register` — Register new user + tenant
- `POST /login` — Login, returns access + refresh token
- `POST /token/refresh` — Refresh access token

### Email Verification (`/api/v1/email`)
- `POST /verify` — Confirm email with token
- `POST /resend-verification` — Request new verification email

### User Invitations (`/api/v1/invitations`)
- `POST /send` — Admin sends invitation
- `POST /accept` — Invitee accepts invitation + creates account
- `GET /{id}` — Get invitation details (pre-acceptance)

### MFA (`/api/v1/mfa`)
- `POST /setup` — Initiate MFA, returns secret + QR code
- `POST /confirm` — Confirm MFA with TOTP code
- `POST /disable` — Disable MFA for current user
- `POST /login` — Complete login with TOTP code

### Users (`/api/v1/users`)
- `GET /me` — Get current user profile
- `PATCH /me` — Update current user
- `GET /` — List users in tenant (requires Admin role)

---

## Testing

### Run All Tests
```bash
# Verbose output
uv run pytest -v

# With coverage
uv run pytest --cov=app tests/

# Specific test file
uv run pytest tests/test_email_verification.py -v

# Specific test
uv run pytest tests/test_mfa.py::test_mfa_setup -v
```

### Test Structure
```
tests/
├── conftest.py              # Fixtures (db, users, tokens)
├── test_auth.py             # Auth endpoints (login, register, refresh)
├── test_email_verification.py  # Email verification flows
├── test_user_invitation.py     # Invitation flows
├── test_mfa.py              # MFA setup, confirm, login
└── test_p2_integration.py   # End-to-end P2 workflows
```

### Key Fixtures
```python
# In conftest.py
@pytest_asyncio.fixture
async def db_session():
    """Async database session for testing"""
    
@pytest_asyncio.fixture
async def test_user(db_session):
    """Test user with verified email"""
    
@pytest_asyncio.fixture
async def test_tenant(db_session):
    """Test tenant"""
    
@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Authorization headers with valid JWT"""
```

### Example Test
```python
async def test_email_verification_flow(client, test_user, db_session):
    # Setup: Create verification token
    token = await create_email_token(db_session, test_user.id, test_user.email)
    
    # Action: Verify email
    response = client.post("/api/v1/email/verify", json={"token": token})
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"
    
    # Verify database updated
    await db_session.refresh(test_user)
    assert test_user.email_verified_at is not None
```

---

## Code Quality

### Linting
```bash
# Check code style
uv run ruff check .

# Auto-fix style issues
uv run ruff format .

# Type checking
uv run mypy app
```

### Standards
- **Line length**: 100 characters
- **Python version**: 3.12
- **Import order**: isort (stdlib → third-party → local)
- **Type hints**: Strict, all public functions typed

---

## P1: Multi-Tenant Auth & RBAC

### Multi-Tenancy (RLS)
- All operational tables include `tenant_id UUID NOT NULL`
- PostgreSQL Row-Level Security (RLS) policies isolate data per tenant
- Backend sets `app.current_tenant` context variable on every request
- Decorator pattern validates tenant ownership (defense in depth)

### User Roles (RBAC)
- **Admin** — Full access to tenant settings, users, invitations
- **Member** — Read/write access to operational data (equipment, orders, etc.)
- **Viewer** — Read-only access to dashboards and reports

### Schemas
```python
# User with role + tenant info
class UserRead(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    email_verified_at: datetime | None = None
    mfa_enabled: bool = False
    roles: list[RoleRead]
    tenant: TenantRead
```

---

## P2: Email Verification, User Invitation & MFA

### Email Verification
- Users must verify email post-registration
- Verification tokens expire after **24 hours**
- Endpoint: `POST /api/v1/email/verify` with token
- Resend endpoint: `POST /api/v1/email/resend-verification` (rate-limited, 3/hour)

### User Invitations
- Admins invite new users via `POST /api/v1/invitations/send`
- Invitations expire after **7 days**
- Invitees accept via `POST /api/v1/invitations/accept` with token
- Accepted invitations create user accounts with assigned roles

### MFA (TOTP)
- Setup: `POST /api/v1/mfa/setup` → returns secret + QR code
- Confirm: `POST /api/v1/mfa/confirm` with TOTP code
- Login: If MFA enabled, `POST /auth/login` returns `mfa_required: true`
- Complete MFA: `POST /api/v1/mfa/login` with challenge token + TOTP code

### Environment Variables
```bash
# Email service (Resend)
RESEND_API_KEY=your_resend_api_key
EMAILS_FROM=noreply@yourdomain.com
EMAILS_FROM_NAME="FleetOps"

# MFA settings
MFA_WINDOW=1  # Time window for TOTP validation (periods)
```

---

## Async Architecture

### Celery Tasks
Tasks are defined in `app/tasks/` and dispatched via Redis:

```python
# Send verification email asynchronously
from app.tasks.email import send_email_verification

send_email_verification.delay(user_id=str(user.id), email=user.email, token=token)
```

### Running Celery Worker
```bash
# In separate terminal
uv run celery -A app.tasks worker --loglevel=info

# With hot-reload (development)
uv run celery -A app.tasks worker --loglevel=info --autoreload
```

---

## Database Migrations

### Alembic
Migrations live in `alembic/versions/`. Generated via SQLAlchemy autogenerate.

### Create Migration
```bash
# Auto-detect model changes
uv run alembic revision --autogenerate -m "add email verification table"

# Edit migration file (review before applying)
# Then apply:
uv run alembic upgrade head
```

### Downgrade
```bash
# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade <revision_id>
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, route registration
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py      # Auth endpoints
│   │       ├── email.py     # Email verification endpoints
│   │       ├── invitations.py   # Invitation endpoints
│   │       ├── mfa.py       # MFA endpoints
│   │       ├── users.py     # User endpoints
│   │       └── __init__.py  # APIRouter aggregation
│   ├── models/
│   │   ├── base.py          # Base model + UUID, timestamps
│   │   ├── user.py          # User model
│   │   ├── tenant.py        # Tenant model
│   │   ├── email_verification.py  # EmailVerificationToken
│   │   ├── user_invitation.py     # UserInvitation
│   │   └── __init__.py      # Model aggregation
│   ├── schemas/
│   │   ├── auth.py          # Auth request/response schemas
│   │   ├── email.py         # Email verification schemas
│   │   ├── invitations.py   # Invitation schemas
│   │   ├── mfa.py           # MFA schemas
│   │   └── user.py          # User schemas
│   ├── services/
│   │   ├── email_service.py # Email delivery (Resend)
│   │   ├── token_service.py # Token generation + hashing
│   │   ├── mfa_service.py   # TOTP + QR code generation
│   │   ├── user_service.py  # User CRUD + role management
│   │   └── invitation_service.py # Invitation CRUD
│   ├── tasks/
│   │   └── email.py         # Celery tasks for email
│   ├── core/
│   │   ├── config.py        # Environment variables
│   │   ├── security.py      # JWT, password hashing
│   │   └── deps.py          # Dependency injection + decorators
│   └── utils/
│       ├── logger.py        # Logging setup
│       └── exceptions.py    # Custom exceptions
├── alembic/
│   ├── env.py               # Alembic environment
│   ├── script.py.mako       # Migration template
│   └── versions/            # Migration files
│       ├── 0001_p1_initial.py
│       ├── 0002_p1_rbac.py
│       └── 0003_p2_email_mfa.py
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py
│   ├── test_email_verification.py
│   ├── test_user_invitation.py
│   ├── test_mfa.py
│   └── test_p2_integration.py
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Dependencies + tool config
├── uv.lock                  # Locked dependency versions
└── Dockerfile               # Docker image definition
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps

# View database logs
docker compose logs postgres

# Recreate database
docker compose down -v
docker compose up -d postgres
uv run alembic upgrade head
```

### Celery Not Picking Up Tasks
```bash
# Check if Redis is running
docker compose ps

# Check if Celery worker is running
ps aux | grep celery

# View Celery worker logs
uv run celery -A app.tasks worker --loglevel=debug
```

### Type Checking Errors
```bash
# Run mypy in strict mode
uv run mypy app --strict

# Fix common issues
uv run mypy app --show-error-codes | grep error
```

### Tests Failing

```bash
# Run tests with full output
uv run pytest tests/ -vv --tb=long

# Check fixtures are properly scoped
uv run pytest tests/conftest.py -v

# Drop test database and retry
docker compose exec postgres dropdb fleet_ops_test
uv run pytest tests/ -v
```

---

## Security Best Practices

1. **Never commit secrets** — Use `.env` (gitignored), never hardcode API keys
2. **Token hashing** — Verification + invitation tokens are SHA-256 hashed before storage
3. **Password hashing** — Argon2id via `passlib`, never stored in plaintext
4. **JWT tokens** — 15-minute expiry (access) + 7-day refresh; use RS256 in production
5. **RLS enforcement** — All queries filtered by `tenant_id` + decorated with `@validate_tenant`
6. **Rate limiting** — Email resend limited to 3/hour per user
7. **Token expiration** — Verification (24h), Invitations (7d), MFA challenge (5min)

---

## Deployment

### Docker
```bash
# Build image
docker build -t fleet-ops-backend:latest .

# Run container
docker run -e DATABASE_URL=... -p 8000:8000 fleet-ops-backend:latest
```

### Production Checklist
- [ ] `.env` configured with production values
- [ ] Database migrated: `alembic upgrade head`
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Linting clean: `ruff check .` + `mypy app`
- [ ] Celery workers running (separate process or container)
- [ ] Redis persistence enabled
- [ ] HTTPS/TLS enabled
- [ ] Monitoring configured (logs, metrics, error tracking)
- [ ] Backups automated

---

## References

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- PostgreSQL RLS: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Celery: https://docs.celeryproject.org/
- pyotp (TOTP): https://pyauth.github.io/pyotp/
- Resend (Email): https://resend.com/docs
