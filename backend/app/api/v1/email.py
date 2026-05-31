from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_tenant_id
from app.core.config import settings
from app.core.database import get_session
from app.services.token_service import TokenService
from app.tasks.email import send_email_verification

router = APIRouter(prefix="/api/v1/email", tags=["email"])


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationEmailRequest(BaseModel):
    pass


class VerifyEmailResponse(BaseModel):
    message: str


@router.post("/verify", response_model=VerifyEmailResponse)
async def verify_email(
    req: VerifyEmailRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
) -> VerifyEmailResponse:
    """Confirm email verification token."""
    success = await TokenService.confirm_email_token(session, req.token, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    return VerifyEmailResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=VerifyEmailResponse)
async def resend_verification_email(
    req: ResendVerificationEmailRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
) -> VerifyEmailResponse:
    """Resend verification email to current user."""
    if current_user.email_verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    token = await TokenService.create_email_verification_token(
        session, current_user.id, tenant_id, current_user.email
    )

    verify_url_base = f"{settings.FRONTEND_URL}/verify-email"
    send_email_verification.delay(
        user_id=str(current_user.id),
        tenant_id=str(tenant_id),
        email=current_user.email,
        token=token,
        verify_url_base=verify_url_base,
    )

    return VerifyEmailResponse(message="Verification email sent")
