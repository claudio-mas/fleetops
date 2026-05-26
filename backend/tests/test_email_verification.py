import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.token_service import TokenService

pytestmark = pytest.mark.asyncio


async def test_generate_token_creates_opaque_token() -> None:
    """Test generating a token creates an opaque string."""
    token = TokenService.generate_token()
    assert token
    assert len(token) > 20
    assert isinstance(token, str)


async def test_generate_token_is_random() -> None:
    """Test each generated token is unique."""
    token1 = TokenService.generate_token()
    token2 = TokenService.generate_token()
    assert token1 != token2


async def test_token_hash_is_deterministic() -> None:
    """Test token hash is same for same token (SHA-256)."""
    token = "test_token_12345"
    hash1 = TokenService.generate_token_hash(token)
    hash2 = TokenService.generate_token_hash(token)
    assert hash1 == hash2


async def test_token_hash_is_64_chars() -> None:
    """Test SHA-256 hash is 64 hex characters."""
    token = "test_token"
    token_hash = TokenService.generate_token_hash(token)
    assert len(token_hash) == 64
    assert all(c in "0123456789abcdef" for c in token_hash)


async def test_create_and_verify_email_token(
    db: AsyncSession, sample_user
) -> None:
    """Test creating and verifying email token."""
    email = "user@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, sample_user.tenant_id, email
    )
    assert token
    assert len(token) > 20


async def test_verify_email_token_returns_user_and_email(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test verifying token returns correct user_id and email."""
    email = "test-verify@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email
    )

    result = await TokenService.verify_email_token(db, token, tenant.id)
    assert result is not None
    verified_user_id, verified_email = result
    assert verified_user_id == sample_user.id
    assert verified_email == email


async def test_verify_email_token_invalid_token(db: AsyncSession, tenant) -> None:
    """Test verifying with invalid token returns None."""
    result = await TokenService.verify_email_token(db, "invalid_token", tenant.id)
    assert result is None


async def test_verify_email_token_wrong_tenant(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test verifying token with wrong tenant_id returns None."""
    email = "test@example.com"
    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email,
    )

    wrong_tenant_id = uuid4()
    result = await TokenService.verify_email_token(db, token, wrong_tenant_id)
    assert result is None


async def test_verify_email_token_expired(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test verifying expired token returns None."""
    email = "test-expired@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email,
    )

    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token = result.scalars().first()
    verification_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db.commit()

    result = await TokenService.verify_email_token(db, token, tenant.id)
    assert result is None


async def test_verify_email_token_already_confirmed(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test verifying already confirmed token returns None."""
    email = "test-confirmed@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email
    )

    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token = result.scalars().first()
    verification_token.confirmed_at = datetime.now(timezone.utc)
    await db.commit()

    result = await TokenService.verify_email_token(db, token, tenant.id)
    assert result is None


async def test_confirm_email_token_success(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming email token updates user.email_verified_at."""
    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, sample_user.email
    )

    user = await db.get(User, sample_user.id)
    assert user.email_verified_at is None

    success = await TokenService.confirm_email_token(db, token, tenant.id)
    assert success is True

    user = await db.get(User, sample_user.id)
    assert user.email_verified_at is not None
    assert isinstance(user.email_verified_at, datetime)


async def test_confirm_email_token_sets_confirmed_at(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming email token marks it as confirmed."""
    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, sample_user.email,
    )

    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token_before = result.scalars().first()
    assert verification_token_before.confirmed_at is None

    await TokenService.confirm_email_token(db, token, tenant.id)

    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token_after = result.scalars().first()
    assert verification_token_after.confirmed_at is not None


async def test_confirm_email_token_invalid_token(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming invalid token returns False."""
    success = await TokenService.confirm_email_token(
        db, "invalid_token", tenant.id,
    )
    assert success is False


async def test_confirm_email_token_expired_token(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming expired token returns False."""
    email = "test-expired-confirm@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email, expires_in_hours=0
    )

    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token = result.scalars().first()
    verification_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db.commit()

    success = await TokenService.confirm_email_token(db, token, tenant.id)
    assert success is False


async def test_confirm_email_token_already_confirmed(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming already confirmed token returns False."""
    email = "test-already-confirmed@example.com"

    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, email
    )

    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    verification_token = result.scalars().first()
    verification_token.confirmed_at = datetime.now(timezone.utc)
    await db.commit()

    success = await TokenService.confirm_email_token(db, token, tenant.id)
    assert success is False


async def test_token_hash_uniqueness(db: AsyncSession, sample_user: User, tenant) -> None:
    """Test that different tokens produce different hashes."""
    token1 = TokenService.generate_token()
    token2 = TokenService.generate_token()

    hash1 = TokenService.generate_token_hash(token1)
    hash2 = TokenService.generate_token_hash(token2)

    assert hash1 != hash2


async def test_create_multiple_tokens_for_same_user(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test creating multiple tokens for the same user."""
    token1 = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, "email1@example.com",
    )
    token2 = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, "email2@example.com",
    )

    assert token1 != token2

    result1 = await TokenService.verify_email_token(db, token1, tenant.id)
    result2 = await TokenService.verify_email_token(db, token2, tenant.id)

    assert result1 is not None
    assert result2 is not None
    assert result1[1] == "email1@example.com"
    assert result2[1] == "email2@example.com"


async def test_verify_token_with_custom_expiration(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test creating token with custom expiration time."""
    token = await TokenService.create_email_verification_token(
        db,
        sample_user.id,
        tenant.id,
        "custom@example.com",
        expires_in_hours=48,
    )

    result = await TokenService.verify_email_token(db, token, tenant.id)
    assert result is not None


async def test_confirm_email_token_different_tenant(
    db: AsyncSession, sample_user: User, tenant
) -> None:
    """Test confirming token with wrong tenant_id returns False."""
    token = await TokenService.create_email_verification_token(
        db, sample_user.id, tenant.id, sample_user.email,
    )

    wrong_tenant_id = uuid4()
    success = await TokenService.confirm_email_token(db, token, wrong_tenant_id)
    assert success is False

    user = await db.get(User, sample_user.id)
    assert user.email_verified_at is None
