# P2: Email Verification, User Invitation & MFA Implementation Plan

> **Para agentes agentic:** SUB-SKILL OBRIGATÓRIA: Use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para implementar este plano tarefa por tarefa. Etapas usam sintaxe checkbox (`- [ ]`) para rastreamento.

**Objetivo:** Estender P1 (Multi-tenant Auth & RBAC) com verificação de e-mail, convite de usuários e MFA TOTP, permitindo workflows de onboarding seguro e optional/obrigatório MFA.

**Arquitetura:** 
- Backend: Novo modelo `EmailVerificationToken` + extensão do modelo `User` com campos `email_verified_at`, `mfa_secret`, `mfa_enabled`. Nova tabela `UserInvitation` para convites. Celery task para enviar e-mails assincronamente. Rotas para confirmar e-mail, aceitar convite, setup/validação MFA.
- Frontend: Nova página `VerifyEmail` com link confirma/resend, página `AcceptInvitation` para novos convidados, fluxo `MFASetup` com QR code (qrcode.react), fluxo `MFALogin` solicitando código TOTP durante login.
- DB: RLS aplicada a `user_invitation`, `email_verification_token`. Tenant settings expandidos com `mfa_policy` (OPTIONAL/REQUIRED).

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Celery + FastAPI Users (com suporte built-in a TOTP), React + TanStack Query + Zustand, PostgreSQL 16 RLS, python-jose + pyotp (TOTP), qrcode.react + qrcode.svg (QR frontend).

---

## File Structure

### Backend Files

**New:**
- `backend/app/models/email_verification.py` — `EmailVerificationToken` model
- `backend/app/models/user_invitation.py` — `UserInvitation` model  
- `backend/app/services/email_service.py` — `EmailService` abstração + tasks Celery
- `backend/app/services/mfa_service.py` — `MFAService` para setup/validação TOTP
- `backend/app/api/v1/email.py` — rotas email verification
- `backend/app/api/v1/invitations.py` — rotas user invitations
- `backend/alembic/versions/0003_p2_email_verification_invitations_mfa.py` — migration

**Modify:**
- `backend/app/models/user.py` — adicionar `email_verified_at`, `mfa_secret`, `mfa_enabled`
- `backend/app/schemas/auth.py` — adicionar schemas para MFA setup/validation
- `backend/app/api/v1/auth.py` — estender login para solicitar MFA se ativado
- `backend/app/api/deps.py` — adicionar `require_email_verified` decorator
- `backend/app/main.py` — registrar rotas novas
- `backend/tests/conftest.py` — helpers para gerar tokens, mockar e-mail
- `backend/pyproject.toml` — adicionar `pyotp`, `qrcode`, `python-multipart` (para upload)

### Frontend Files

**New:**
- `frontend/src/pages/VerifyEmail.tsx` — confirmação de e-mail com resend
- `frontend/src/pages/AcceptInvitation.tsx` — aceitar convite
- `frontend/src/pages/MFASetup.tsx` — setup TOTP com QR code
- `frontend/src/components/MFALoginForm.tsx` — solicitar código TOTP no login
- `frontend/src/hooks/useEmailVerification.ts` — API calls email verification
- `frontend/src/hooks/useMFA.ts` — API calls MFA setup/validation
- `frontend/src/hooks/useInvitation.ts` — API calls invitations
- `frontend/src/stores/mfa.ts` — estado MFA em Zustand
- `frontend/src/types/mfa.ts` — tipos MFA

**Modify:**
- `frontend/src/pages/Login.tsx` — integrar form MFA
- `frontend/src/pages/Register.tsx` — redirecionar para verify-email após signup
- `frontend/src/hooks/useAuth.ts` — adicionar chamada email verification
- `frontend/src/types/auth.ts` — estender `UserRead` com `email_verified_at`, `mfa_enabled`

### Test Files

- `backend/tests/test_email_verification.py` — testes verify, resend, expired token
- `backend/tests/test_user_invitation.py` — testes invite, accept, rejection
- `backend/tests/test_mfa.py` — testes setup, validation, required policy, disabled

---

## Tasks

### Task 1: Database Migration — Email Verification, Invitations, MFA

**Files:**
- Create: `backend/alembic/versions/0003_p2_email_verification_invitations_mfa.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Extend User model with email_verified_at, mfa_secret, mfa_enabled**

Open `backend/app/models/user.py` and add columns:

```python
# In the User class, add after password_hash:
email_verified_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True), nullable=True, default=None
)
mfa_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 2: Create EmailVerificationToken model**

Create `backend/app/models/email_verification.py`:

```python
from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.models.base import Base


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_token"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 3: Create UserInvitation model**

Create `backend/app/models/user_invitation.py`:

```python
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.models.base import Base


class InvitationStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class UserInvitation(Base):
    __tablename__ = "user_invitation"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    invited_by_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("role.id"), nullable=False)
```

- [ ] **Step 4: Update models/__init__.py to export new models**

Open `backend/app/models/__init__.py` and add:

```python
from app.models.email_verification import EmailVerificationToken
from app.models.user_invitation import UserInvitation, InvitationStatus
```

- [ ] **Step 5: Write Alembic migration**

Create `backend/alembic/versions/0003_p2_email_verification_invitations_mfa.py` with schema changes for email_verified_at, mfa_secret, mfa_enabled columns and new tables.

- [ ] **Step 6: Run migration locally and verify**

```bash
cd backend
uv run alembic upgrade head
```

Expected: Migration applies without error, columns/tables created.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/email_verification.py backend/app/models/user_invitation.py backend/app/models/user.py backend/app/models/__init__.py backend/alembic/versions/0003_*.py
git commit -m "feat(db): add email verification, invitations, MFA columns and tables"
```

---

### Task 2: Email Service — Abstraction + Celery Tasks

**Files:**
- Create: `backend/app/services/email_service.py`
- Create: `backend/app/tasks/email.py`
- Modify: `backend/pyproject.toml` (add dependencies)
- Modify: `backend/app/core/config.py` (email settings)

Implement EmailService abstraction with Resend provider, add Celery email tasks (send_email_verification, send_user_invitation), add configuration for SMTP/Resend.

---

### Task 3: Email Verification Flow — Backend Models, Service, Tests

**Files:**
- Create: `backend/app/services/token_service.py`
- Create: `backend/tests/test_email_verification.py`

Implement TokenService with generate_token, verify_email_token, confirm_email_token methods. Write tests for token creation, validation, expiration.

---

### Task 4: Email Verification API Routes

**Files:**
- Create: `backend/app/api/v1/email.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/v1/auth.py`

Add POST /api/v1/email/verify and POST /api/v1/email/resend-verification endpoints. Update register flow to send verification email.

---

### Task 5: User Invitation — Backend Model, Service, Tests

**Files:**
- Modify: `backend/app/services/token_service.py` (add invitation methods)
- Create: `backend/tests/test_user_invitation.py`

Add create_user_invitation, get_invitation_by_token, accept_invitation methods to TokenService. Write tests for invitation flow.

---

### Task 6: User Invitation API Routes

**Files:**
- Create: `backend/app/api/v1/invitations.py`
- Modify: `backend/app/main.py`

Add POST /api/v1/invitations/send and POST /api/v1/invitations/accept endpoints. Require admin role for sending invitations.

---

### Task 7: MFA Service — TOTP Setup, Validation, Tests

**Files:**
- Create: `backend/app/services/mfa_service.py`
- Create: `backend/tests/test_mfa.py`

Implement MFAService with generate_secret, get_totp, verify_token, setup_mfa, confirm_mfa, validate_mfa_login, disable_mfa methods using pyotp. Write comprehensive tests.

---

### Task 8: MFA API Routes — Setup, Login Validation

**Files:**
- Create: `backend/app/api/v1/mfa.py`
- Modify: `backend/app/api/v1/auth.py` (extend login with MFA)
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas/auth.py`

Add POST /api/v1/mfa/setup, /mfa/confirm, /mfa/disable, /mfa/login endpoints. Extend login to check mfa_required and issue mfa_challenge_token. Support tenant mfa_policy (optional/required).

---

### Task 9: Frontend — Email Verification Page

**Files:**
- Create: `frontend/src/pages/VerifyEmail.tsx`
- Create: `frontend/src/hooks/useEmailVerification.ts`
- Modify: `frontend/src/App.tsx` (add route)
- Modify: `frontend/src/pages/Register.tsx` (redirect after signup)

Create VerifyEmail page with token verification and resend functionality. Redirect from register on signup success.

---

### Task 10: Frontend — MFA Setup Page

**Files:**
- Create: `frontend/src/pages/MFASetup.tsx`
- Create: `frontend/src/hooks/useMFA.ts`
- Create: `frontend/src/stores/mfa.ts`
- Modify: `frontend/src/App.tsx` (add route)
- Modify: `frontend/src/pages/Dashboard.tsx` (add MFA settings link)

Create MFASetup page with QR code display and TOTP code entry. Show instructions for scanning with authenticator app.

---

### Task 11: Frontend — MFA Login Form

**Files:**
- Create: `frontend/src/components/MFALoginForm.tsx`
- Modify: `frontend/src/pages/Login.tsx`

Create MFALoginForm component. Update Login page to show MFA challenge after initial login if mfa_required is true.

---

### Task 12: Integration Tests — Full P2 Flows

**Files:**
- Create: `backend/tests/test_p2_integration.py`

Write end-to-end integration tests covering: signup → email verification → login, mfa setup → confirmation → login with mfa.

---

### Task 13: Documentation & Code Review

**Files:**
- Modify: `backend/README.md` or create `docs/P2_EMAIL_MFA.md`

Document email configuration, email verification flow, user invitation flow, and MFA setup. Code review for security, consistency, edge cases.

---

## Execution Notes

- All 13 tasks must complete before branch can merge
- Each task includes TDD (write tests first, implement to pass)
- Commit after each task for clean history
- Database migration (Task 1) must run before any other task
- Backend tasks (1-8, 12-13) are independent after Task 1
- Frontend tasks (9-11) can proceed in parallel with backend
- Task 12 integration tests validate end-to-end flows
