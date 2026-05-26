import base64
from io import BytesIO
from uuid import UUID

import pyotp
import qrcode
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class MFAService:
    """Service for TOTP setup and validation."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret (32 bytes base32-encoded)."""
        return pyotp.random_base32()

    @staticmethod
    def get_totp(secret: str) -> pyotp.TOTP:
        """Get TOTP object for a secret."""
        return pyotp.TOTP(secret)

    @staticmethod
    def get_provisioning_uri(
        secret: str, email: str, issuer: str = "FleetOps"
    ) -> str:
        """Generate provisioning URI for QR code."""
        totp = MFAService.get_totp(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)

    @staticmethod
    def generate_qr_code(provisioning_uri: str) -> str:
        """Generate QR code as data URI PNG."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_data = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_data}"

    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """Verify if a TOTP token is valid (with ±1 period window for clock skew)."""
        totp = MFAService.get_totp(secret)
        try:
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    @staticmethod
    async def setup_mfa(
        session: AsyncSession,
        user_id: UUID,
    ) -> tuple[str, str]:
        """Setup MFA for user. Returns (secret, qr_code_data_uri)."""
        secret = MFAService.generate_secret()

        user = await session.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        provisioning_uri = MFAService.get_provisioning_uri(secret, user.email)
        qr_code_data_uri = MFAService.generate_qr_code(provisioning_uri)

        return secret, qr_code_data_uri

    @staticmethod
    async def confirm_mfa(
        session: AsyncSession,
        user_id: UUID,
        secret: str,
        token: str,
    ) -> bool:
        """Confirm MFA setup by verifying token, then persist secret."""
        if not MFAService.verify_token(secret, token):
            return False

        user = await session.get(User, user_id)
        if not user:
            return False

        user.mfa_secret = secret
        user.mfa_enabled = True
        await session.commit()

        return True

    @staticmethod
    async def validate_mfa_login(
        session: AsyncSession,
        user_id: UUID,
        token: str,
    ) -> bool:
        """Validate MFA token during login."""
        user = await session.get(User, user_id)
        if not user or not user.mfa_enabled or not user.mfa_secret:
            return False

        return MFAService.verify_token(user.mfa_secret, token)

    @staticmethod
    async def disable_mfa(
        session: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """Disable MFA for user."""
        user = await session.get(User, user_id)
        if not user:
            return False

        user.mfa_secret = None
        user.mfa_enabled = False
        await session.commit()

        return True
