from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.models.role import RoleName
from app.models.user_invitation import InvitationStatus, UserInvitation
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


async def test_invitation_status_enum() -> None:
    """Test InvitationStatus enum values."""
    assert InvitationStatus.PENDING.value == "pending"
    assert InvitationStatus.ACCEPTED.value == "accepted"
    assert InvitationStatus.REJECTED.value == "rejected"
    assert InvitationStatus.EXPIRED.value == "expired"


async def test_create_user_invitation_returns_token(db, sample_user, tenant):
    """Test create_user_invitation returns a raw token."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.ADMIN,
    )

    assert token
    assert len(token) > 20
    assert isinstance(token, str)


async def test_create_invitation_with_custom_expiration(
    db, sample_user, tenant
):
    """Test creating invitation with custom expiration."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.GESTOR,
        expires_in_days=14,
    )

    invitation = await TokenService.get_invitation_by_token(db, token)
    assert invitation is not None


async def test_get_invitation_by_token(db, sample_user, tenant):
    """Test retrieving invitation by token."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.OPERADOR,
    )

    invitation = await TokenService.get_invitation_by_token(db, token)
    assert invitation is not None
    assert invitation.email == "newuser@example.com"
    assert invitation.status == InvitationStatus.PENDING
    assert invitation.invited_by_id == sample_user.id


async def test_get_invitation_invalid_token(db):
    """Test retrieving invitation with invalid token returns None."""
    invitation = await TokenService.get_invitation_by_token(
        db, "invalid_token"
    )
    assert invitation is None


async def test_get_invitation_expired(db, sample_user, tenant):
    """Test retrieving expired invitation returns None and marks as
    EXPIRED."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.MECANICO,
        expires_in_days=0,
    )

    # Manually expire the invitation
    token_hash = TokenService.generate_token_hash(token)
    await db.execute(
        update(UserInvitation)
        .where(UserInvitation.token_hash == token_hash)
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await db.commit()

    # Try to retrieve
    invitation = await TokenService.get_invitation_by_token(db, token)
    assert invitation is None


async def test_accept_invitation(db, sample_user, tenant):
    """Test accepting invitation updates status and user ID."""
    import fastapi_users.schemas as fau_schemas
    from uuid6 import uuid7

    from app.services.user_manager import get_user_db, get_user_manager

    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.ADMIN,
    )

    # Create a new user for acceptance
    class _UC(fau_schemas.BaseUserCreate):
        tenant_id: str
        full_name: str

    async for user_db_inst in get_user_db(db):
        async for mgr in get_user_manager(user_db_inst):
            new_user = await mgr.create(
                _UC(
                    email=f"accepted-{uuid7().hex[:8]}@test.com",
                    password="SenhaForte123!",
                    tenant_id=str(tenant.id),
                    full_name="Accepted User",
                )
            )

    # Accept invitation
    success = await TokenService.accept_invitation(db, token, new_user.id)
    assert success is True

    # Verify invitation was updated
    token_hash = TokenService.generate_token_hash(token)
    result = await db.execute(
        select(UserInvitation).where(
            UserInvitation.token_hash == token_hash
        )
    )
    invitation = result.scalars().first()

    assert invitation.status == InvitationStatus.ACCEPTED
    assert invitation.accepted_user_id == new_user.id
    assert invitation.accepted_at is not None


async def test_accept_invitation_invalid_token(db):
    """Test accepting invalid token returns False."""
    from uuid import uuid4

    new_user_id = uuid4()

    success = await TokenService.accept_invitation(
        db, "invalid_token", new_user_id
    )
    assert success is False


async def test_accept_invitation_expired(db, sample_user, tenant):
    """Test accepting expired invitation returns False."""
    from uuid import uuid4

    new_user_id = uuid4()

    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="newuser@example.com",
        role_name=RoleName.LEITURA,
    )

    # Expire it
    token_hash = TokenService.generate_token_hash(token)
    await db.execute(
        update(UserInvitation)
        .where(UserInvitation.token_hash == token_hash)
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await db.commit()

    # Try to accept
    success = await TokenService.accept_invitation(db, token, new_user_id)
    assert success is False


async def test_create_multiple_invitations_same_tenant(
    db, sample_user, tenant
):
    """Test creating multiple invitations for different users in same
    tenant."""
    token1 = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="user1@example.com",
        role_name=RoleName.ADMIN,
    )

    token2 = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="user2@example.com",
        role_name=RoleName.GESTOR,
    )

    assert token1 != token2

    inv1 = await TokenService.get_invitation_by_token(db, token1)
    inv2 = await TokenService.get_invitation_by_token(db, token2)

    assert inv1.email == "user1@example.com"
    assert inv2.email == "user2@example.com"


async def test_invitation_persists_correctly(db, sample_user, tenant):
    """Test that invitation data persists correctly."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="test@example.com",
        role_name=RoleName.OPERADOR,
        expires_in_days=5,
    )

    invitation = await TokenService.get_invitation_by_token(db, token)

    assert invitation.tenant_id == tenant.id
    assert invitation.invited_by_id == sample_user.id
    assert invitation.email == "test@example.com"
    assert invitation.role_name == RoleName.OPERADOR
    assert invitation.status == InvitationStatus.PENDING
    assert invitation.accepted_at is None
    assert invitation.accepted_user_id is None


async def test_expired_invitation_not_retrievable_after_mark(
    db, sample_user, tenant
):
    """Test that expired invitation cannot be retrieved even by direct
    query."""
    token = await TokenService.create_user_invitation(
        db,
        tenant_id=tenant.id,
        invited_by_id=sample_user.id,
        email="test@example.com",
        role_name=RoleName.MECANICO,
    )

    # Expire it
    token_hash = TokenService.generate_token_hash(token)
    await db.execute(
        update(UserInvitation)
        .where(UserInvitation.token_hash == token_hash)
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await db.commit()

    # Retrieve via get_invitation_by_token (should be None)
    invitation = await TokenService.get_invitation_by_token(db, token)
    assert invitation is None

    # Verify it was marked as EXPIRED in DB
    result = await db.execute(
        select(UserInvitation).where(
            UserInvitation.token_hash == token_hash
        )
    )
    db_invitation = result.scalars().first()
    assert db_invitation.status == InvitationStatus.EXPIRED
