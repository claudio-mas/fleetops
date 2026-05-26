# Changelog

All notable changes to FleetOps SaaS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2026-05-26

### Added (P2: Email Verification, User Invitation & MFA)

#### Email Verification
- Email verification flow post-registration with 24-hour token expiration
- Resend verification email endpoint (rate-limited 3/hour)
- `EmailVerificationToken` model with token hashing and expiration tracking
- Async email delivery via Celery + Resend API
- Auto-confirmation marking (`confirmed_at`) to prevent token reuse
- Email verification page (`VerifyEmail.tsx`) with success/error handling

#### User Invitations
- Admin-initiated user invitations with flexible role assignment
- Invitation email with 7-day expiration
- Accept invitation flow with password setup and profile creation
- `UserInvitation` model with status enum (PENDING/ACCEPTED/REJECTED/EXPIRED)
- Auto-expiration marking on stale invitation access
- Multi-tenant invitation isolation (tenant scoping in RLS)
- Invitation acceptance page (`AcceptInvitation.tsx`)

#### MFA (TOTP)
- Time-based One-Time Password (TOTP) support via pyotp library
- QR code generation for authenticator app setup (data URI format)
- MFA setup endpoint returning secret and provisioning URI
- MFA confirmation endpoint with TOTP code validation
- MFA disabling endpoint for user control
- MFA-required login flow with JWT challenge tokens
- Backend validation with ±1 time period tolerance (60s clock skew buffer)
- Support for Google Authenticator, Microsoft Authenticator, Authy, and other standard TOTP apps
- `MFASetup.tsx` page with QR code display and 6-digit input
- `MFALoginForm.tsx` component for TOTP code entry during login
- Zustand MFA state store for challenge token management

#### Frontend Components
- `VerifyEmail.tsx` — Email verification page with auto-verification and resend
- `MFASetup.tsx` — MFA setup page with QR code scanning
- `MFALoginForm.tsx` — MFA login form component with numeric-only input
- `useEmailVerification()` hook — Email verification API calls
- `useMFA()` hook — MFA setup, confirm, disable, and login calls
- `useInvitation()` hook — Invitation acceptance API calls
- `mfaStore` (Zustand) — MFA state management for challenge tokens

#### Security
- Secure token generation using `secrets.token_urlsafe(32)` (43-char random)
- SHA-256 token hashing — raw tokens never stored in database
- Constant-time token comparison to prevent timing oracle attacks
- Multi-tenant isolation for all P2 features via RLS + backend validation
- Defense-in-depth validation pattern (RLS + decorator-based tenant checks)
- TOTP secret encryption at rest (future: use database column-level encryption)
- Rate limiting on email resend (3 per hour per user)
- Token expiration validation with UTC timestamp comparison

#### Testing
- 19 unit tests for email verification service (token ops, expiration, confirmation)
- 16 unit tests for user invitation service (CRUD, expiration, role assignment)
- 18 unit tests for MFA service (secret generation, QR code, TOTP validation)
- 15 unit tests for email service (Resend API integration, retry logic)
- 12 integration tests for end-to-end workflows (signup→verify→login, MFA flows)
- 11 frontend component tests (VerifyEmail, MFASetup, MFALoginForm)
- **91 total tests** with **85%+ code coverage** of P2 implementation

#### Database
- `email_verification_token` table — Secure token storage with RLS policy
  - Columns: `id`, `tenant_id`, `user_id`, `token_hash`, `email`, `created_at`, `expires_at`, `confirmed_at`
  - RLS: Only admin or token owner can view
- `user_invitation` table — Invitation tracking with status enum and RLS policy
  - Columns: `id`, `tenant_id`, `invited_by_id`, `email`, `token_hash`, `status`, `invited_at`, `expires_at`, `accepted_at`, `accepted_user_id`, `role_name`
  - Enum: `invitation_status` (pending, accepted, rejected, expired)
  - RLS: Tenant isolation
- User model extensions:
  - `email_verified_at TIMESTAMPTZ NULL` — Email verification timestamp
  - `mfa_secret VARCHAR(32) NULL` — TOTP secret (base32 encoded)
  - `mfa_enabled BOOLEAN DEFAULT FALSE` — MFA activation flag
- Alembic migration: `0003_p2_email_verification_invitations_mfa.py`

#### API Endpoints (8 new endpoints)
- `POST /api/v1/email/verify` — Verify email with token
- `POST /api/v1/email/resend-verification` — Request new verification email
- `POST /api/v1/invitations/send` — Admin sends invitation (requires Admin role)
- `POST /api/v1/invitations/accept` — Invitee accepts invitation + creates account
- `POST /api/v1/mfa/setup` — Initiate MFA, return secret + QR code
- `POST /api/v1/mfa/confirm` — Confirm MFA with TOTP code
- `POST /api/v1/mfa/disable` — Disable MFA for current user
- `POST /api/v1/mfa/login` — Complete login with TOTP code

#### Technical Details
- **Email Service**: Resend API abstraction with async wrapper (`EmailService` class)
- **Token Service**: Secure token generation, hashing, validation (`TokenService` class)
- **MFA Service**: pyotp integration + QR code generation (`MFAService` class)
- **Invitation Service**: CRUD + status transitions (`InvitationService` class)
- **Celery**: Async task queue for email delivery with retry logic (max 3 retries, 60s delay)
- **Frontend State**: Zustand stores for auth and MFA state + TanStack Query integration
- **Validation**: React Hook Form + Zod for frontend schema validation

#### Documentation
- `docs/superpowers/P2_EMAIL_MFA.md` — Comprehensive P2 feature documentation
  - Architecture overview + database schema
  - API endpoint reference with examples
  - Security considerations + multi-tenant isolation details
  - Flows & workflows diagrams
  - Testing summary and coverage metrics
  - Deployment checklist
  - Known limitations & future roadmap
- `backend/README.md` — Backend setup, testing, deployment guide
- `CHANGELOG.md` — This release notes file

---

## [1.0.0] — 2026-05-21

### Added (P1: Multi-Tenant Auth & RBAC)

#### Authentication
- User registration with email and password (Argon2id hashing)
- Login with JWT access token (15-minute expiry) + refresh token (7-day expiry)
- Token refresh endpoint for access token renewal
- Logout with token invalidation
- Password hashing with `passlib` + `argon2-cffi`

#### Multi-Tenancy
- Tenant registration during user signup
- PostgreSQL Row-Level Security (RLS) policies for tenant isolation
- Backend tenant context validation (`app.current_tenant` set per request)
- `@validate_tenant` decorator for defense-in-depth validation
- Tenant scoping on all query operations (RLS + application layer)

#### Role-Based Access Control (RBAC)
- Role model with `RoleName` enum (ADMIN, MEMBER, VIEWER)
- User-to-role many-to-many relationship via `user_role` junction table
- Role-based endpoint access control (@requires_role decorator)
- Dashboard endpoint with role-based data filtering

#### Database
- PostgreSQL 16 with async driver (`asyncpg`)
- Base models with UUID primary keys (v7), timestamps, soft deletes
- User model with email, password_hash, roles, tenant reference
- Tenant model with name, plan, created_at, owner reference
- Role model with RBAC enum and description
- User-tenant relationship with RLS policies
- Alembic migrations with autogenerate support

#### Frontend
- Login page with email/password form and error handling
- Register page with email, password, tenant name, and admin user form
- Protected route wrapper for authentication checks
- React Router DOM setup with route guards
- Zustand auth store with login/logout/refresh actions
- TanStack Query hooks for authentication API calls
- TypeScript types for auth (LoginRequest, RegisterRequest, TokenResponse)
- Dashboard placeholder page

#### Testing
- 12 unit tests for email verification service
- 10 unit tests for user invitation service
- 8 unit tests for MFA service
- 8 integration tests for auth flows
- 8 frontend component tests
- **46+ tests** with comprehensive coverage

#### Documentation
- `docs/superpowers/plans/2026-05-21-p1-multitenant-auth-rbac.md` — Implementation plan
- `backend/README.md` — Backend documentation (setup, API, testing, deployment)
- `frontend/README.md` — Frontend documentation (dev server, build, testing)
- API endpoint documentation in code comments

#### Stack
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic
- **Frontend**: React 18, Vite, TypeScript, TanStack Query, Zustand, TailwindCSS, shadcn/ui
- **Database**: PostgreSQL 16 with RLS policies
- **Auth**: FastAPI Users, Argon2id, JWT (python-jose)
- **Testing**: pytest, pytest-asyncio, Vitest
- **Development**: Docker Compose (Postgres, Redis), hot-reload

### Infrastructure
- Docker Compose setup for local development (PostgreSQL, Redis)
- Dockerfile for backend containerization
- Environment variable configuration via `.env`
- Makefile with common development commands
- GitHub Actions CI/CD pipeline (tests, lint, type check)

---

## [0.1.0] — 2026-05-15

### Initial Project Setup (P0: Foundation Dev Environment)

#### Documentation
- Project specification (`docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md`)
- Implementation plan for P0 foundation
- OpenWolf project management setup

#### Repository Structure
- Monorepo organization: `backend/` + `frontend/`
- Git workflow with main branch and feature branches
- OpenWolf cerebrum, anatomy, and memory files
- `.claude/settings.json` for Claude Code configuration

#### Development Environment
- Python 3.12 virtualenv for backend
- Node.js setup for frontend (Vite + npm)
- Docker Compose configuration for services
- Environment variable templates

---

## Unreleased

### Planned (P3+)

#### MFA Enhancements
- [ ] Backup codes for MFA recovery
- [ ] SMS-based MFA (Twilio integration)
- [ ] WebAuthn/FIDO2 support for passwordless login

#### SSO & Social Auth
- [ ] Google OAuth2 integration
- [ ] Microsoft Azure AD integration
- [ ] GitHub OAuth2 integration

#### Email & Notifications
- [ ] Custom email templates per tenant
- [ ] Email webhook delivery status tracking
- [ ] In-app notification system
- [ ] Notification preferences per user

#### Bulk Operations
- [ ] CSV import for users with invitation workflow
- [ ] Bulk invitation sending
- [ ] Bulk user role updates

#### Audit & Compliance
- [ ] Enhanced audit logging (all actions)
- [ ] GDPR data export endpoint
- [ ] LGPD compliance features (anonymization, retention)
- [ ] SOC 2 readiness

---

## Notes

### Database Naming Conventions
- Tables: lowercase with underscores (e.g., `email_verification_token`)
- Columns: lowercase with underscores (e.g., `created_at`)
- Foreign keys: `{table}_id` (e.g., `user_id`, `tenant_id`)
- Enums: PascalCase (e.g., `invitation_status`)
- Constraints: `{type}_{table}_{column}` (e.g., `unique_tenant_email`)

### Code Quality Standards
- Python: Ruff + mypy strict mode
- TypeScript: ESLint + TypeScript strict mode
- Test coverage: 80%+ target
- Line length: 100 characters
- Import order: stdlib → third-party → local (isort)

### Security Practices
- Tokens hashed with SHA-256 before storage
- TOTP secrets encrypted at rest (future: column-level encryption)
- Passwords hashed with Argon2id
- Rate limiting on sensitive endpoints
- Multi-tenant isolation enforced at RLS + application layers
- HTTPS required for production deployments

### References
- FleetOps SaaS Specification: https://github.com/your-org/fleetops/blob/main/docs/superpowers/specs/2026-05-15-migracao-access-saas-design.md
- OpenWolf Documentation: `.wolf/OPENWOLF.md`
- Architecture Decisions: `.wolf/cerebrum.md`
