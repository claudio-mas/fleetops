from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.auth import (
    MFAConfirmRequest,
    MFAConfirmResponse,
    MFADisableRequest,
    MFALoginRequest,
    MFALoginResponse,
    MFASetupRequest,
    MFASetupResponse,
)
from app.services.mfa_service import MFAService

router = APIRouter(prefix="/api/v1/mfa", tags=["mfa"])


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    req: MFASetupRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MFASetupResponse:
    """Initiate MFA setup (generate secret + QR code)."""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled",
        )

    secret, qr_code = await MFAService.setup_mfa(session, current_user.id)

    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        message="Scan QR code with authenticator app and confirm with token",
    )


@router.post("/confirm", response_model=MFAConfirmResponse)
async def confirm_mfa(
    req: MFAConfirmRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MFAConfirmResponse:
    """Confirm MFA setup with TOTP code."""
    success = await MFAService.confirm_mfa(
        session, current_user.id, req.secret, req.token
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token or setup failed",
        )

    return MFAConfirmResponse(message="MFA enabled successfully")


@router.post("/disable", response_model=MFAConfirmResponse)
async def disable_mfa(
    req: MFADisableRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MFAConfirmResponse:
    """Disable MFA."""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled",
        )

    success = await MFAService.disable_mfa(session, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA",
        )

    return MFAConfirmResponse(message="MFA disabled successfully")


@router.post("/login", response_model=MFALoginResponse)
async def mfa_login(
    req: MFALoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    x_mfa_challenge: Annotated[str | None, Header()] = None,
) -> MFALoginResponse:
    """Validate MFA token and issue access/refresh tokens."""
    if not x_mfa_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing MFA challenge token",
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA login endpoint requires challenge token decoding",
    )
