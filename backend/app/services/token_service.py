import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerificationToken
from app.models.role import RoleName
from app.models.user import User
from app.models.user_invitation import InvitationStatus, UserInvitation


class TokenService:
    """Service for generating and validating email verification tokens."""

    @staticmethod
    def generate_token_hash(token: str) -> str:
        """Hash a token with SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def generate_token() -> str:
        """Generate an opaque token (32 random bytes base32-encoded)."""
        return secrets.token_urlsafe(32)

    @staticmethod
    async def create_email_verification_token(
        session: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        email: str,
        expires_in_hours: int = 24,
    ) -> str:
        """Create email verification token and return raw token (not hashed)."""
        token = TokenService.generate_token()
        token_hash = TokenService.generate_token_hash(token)

        expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)

        verification_token = EmailVerificationToken(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(verification_token)
        await session.flush()

        return token

    @staticmethod
    async def verify_email_token(
        session: AsyncSession,
        token: str,
        tenant_id: UUID,
    ) -> tuple[UUID, str] | None:
        """Validate token and return (user_id, email) if valid, None otherwise."""
        token_hash = TokenService.generate_token_hash(token)

        result = await session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.tenant_id == tenant_id,
                EmailVerificationToken.confirmed_at.is_(None),
            )
        )
        verification_token = result.scalars().first()

        if not verification_token:
            return None

        if verification_token.expires_at < datetime.now(UTC):
            return None

        return verification_token.user_id, verification_token.email

    @staticmethod
    async def confirm_email_token(
        session: AsyncSession,
        token: str,
        tenant_id: UUID,
    ) -> bool:
        """Mark token as confirmed and update user.email_verified_at."""
        user_id_email = await TokenService.verify_email_token(session, token, tenant_id)
        if not user_id_email:
            return False

        user_id, email = user_id_email

        token_hash = TokenService.generate_token_hash(token)
        result = await session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
        verification_token = result.scalars().first()
        if verification_token is None:
            return False

        verification_token.confirmed_at = datetime.now(UTC)

        user = await session.get(User, user_id)
        if user is None:
            return False

        user.email_verified_at = datetime.now(UTC)

        await session.commit()
        return True

    @staticmethod
    async def create_user_invitation(
        session: AsyncSession,
        tenant_id: UUID,
        invited_by_id: UUID,
        email: str,
        role_name: RoleName,
        expires_in_days: int = 7,
    ) -> str:
        """Create user invitation and return the raw token (not hashed)."""
        token = TokenService.generate_token()
        token_hash = TokenService.generate_token_hash(token)

        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        invitation = UserInvitation(
            tenant_id=tenant_id,
            invited_by_id=invited_by_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            role_name=role_name,
            status=InvitationStatus.PENDING,
        )
        session.add(invitation)
        await session.flush()

        return token

    @staticmethod
    async def get_invitation_by_token(
        session: AsyncSession,
        token: str,
    ) -> UserInvitation | None:
        """Get invitation by token, validating expiration. Returns None if expired/invalid."""
        token_hash = TokenService.generate_token_hash(token)

        result = await session.execute(
            select(UserInvitation).where(
                UserInvitation.token_hash == token_hash,
                UserInvitation.status == InvitationStatus.PENDING,
            )
        )
        invitation = result.scalars().first()

        if not invitation:
            return None

        if invitation.expires_at < datetime.now(UTC):
            invitation.status = InvitationStatus.EXPIRED
            await session.commit()
            return None

        return invitation

    @staticmethod
    async def accept_invitation(
        session: AsyncSession,
        token: str,
        accepted_user_id: UUID,
    ) -> bool:
        """Mark invitation as accepted and link to user."""
        invitation = await TokenService.get_invitation_by_token(session, token)
        if not invitation:
            return False

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_user_id = accepted_user_id
        invitation.accepted_at = datetime.now(UTC)

        await session.commit()
        return True
