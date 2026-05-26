from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.mfa_service import MFAService

pytestmark = pytest.mark.asyncio


async def test_setup_mfa(db: AsyncSession, sample_user):
    """Test MFA setup returns secret and QR code."""
    secret, qr_code = await MFAService.setup_mfa(db, sample_user.id)

    assert secret
    assert len(secret) == 32
    assert qr_code.startswith("data:image/png;base64,")


async def test_setup_mfa_nonexistent_user(db: AsyncSession):
    """Test MFA setup with nonexistent user raises error."""
    with pytest.raises(ValueError, match="User not found"):
        await MFAService.setup_mfa(db, uuid4())


async def test_confirm_mfa(db: AsyncSession, sample_user):
    """Test confirming MFA setup."""
    secret, _ = await MFAService.setup_mfa(db, sample_user.id)

    totp = MFAService.get_totp(secret)
    token = totp.now()

    success = await MFAService.confirm_mfa(db, sample_user.id, secret, token)
    assert success

    user = await db.get(User, sample_user.id)
    assert user.mfa_enabled
    assert user.mfa_secret == secret


async def test_confirm_mfa_invalid_token(db: AsyncSession, sample_user):
    """Test confirming MFA with invalid token."""
    secret, _ = await MFAService.setup_mfa(db, sample_user.id)

    success = await MFAService.confirm_mfa(
        db, sample_user.id, secret, "000000"
    )
    assert not success


async def test_validate_mfa_login(db: AsyncSession, sample_user):
    """Test validating MFA token during login."""
    secret, _ = await MFAService.setup_mfa(db, sample_user.id)
    totp = MFAService.get_totp(secret)
    token = totp.now()

    await MFAService.confirm_mfa(db, sample_user.id, secret, token)

    fresh_token = totp.now()
    valid = await MFAService.validate_mfa_login(db, sample_user.id, fresh_token)
    assert valid


async def test_validate_mfa_login_invalid_token(db: AsyncSession, sample_user):
    """Test validating login with invalid token."""
    secret, _ = await MFAService.setup_mfa(db, sample_user.id)
    totp = MFAService.get_totp(secret)
    token = totp.now()

    await MFAService.confirm_mfa(db, sample_user.id, secret, token)

    invalid = await MFAService.validate_mfa_login(db, sample_user.id, "000000")
    assert not invalid


async def test_validate_mfa_login_mfa_disabled(db: AsyncSession, sample_user):
    """Test validating login when MFA not enabled."""
    valid = await MFAService.validate_mfa_login(db, sample_user.id, "123456")
    assert not valid


async def test_disable_mfa(db: AsyncSession, sample_user):
    """Test disabling MFA."""
    secret, _ = await MFAService.setup_mfa(db, sample_user.id)
    totp = MFAService.get_totp(secret)
    token = totp.now()

    await MFAService.confirm_mfa(db, sample_user.id, secret, token)

    success = await MFAService.disable_mfa(db, sample_user.id)
    assert success

    user = await db.get(User, sample_user.id)
    assert not user.mfa_enabled
    assert user.mfa_secret is None


async def test_disable_mfa_nonexistent_user(db: AsyncSession):
    """Test disabling MFA for nonexistent user."""
    success = await MFAService.disable_mfa(db, uuid4())
    assert not success
