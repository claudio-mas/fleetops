from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_tenant_id
from app.core.config import settings
from app.core.database import get_session
from app.models.role import RoleName, UserRole
from app.services.token_service import TokenService
from app.tasks.email import send_user_invitation

router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


class SendInvitationRequest(BaseModel):
    email: EmailStr
    role: str


class SendInvitationResponse(BaseModel):
    message: str


class AcceptInvitationRequest(BaseModel):
    token: str


class AcceptInvitationResponse(BaseModel):
    message: str
    tenant_id: str


@router.post("/send", response_model=SendInvitationResponse)
async def send_invitation(
    req: SendInvitationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: CurrentUser,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
) -> SendInvitationResponse:
    """Send user invitation (requires admin role)."""
    result = await session.execute(
        select(UserRole).where(
            UserRole.user_id == current_user.id,
            UserRole.tenant_id == tenant_id,
            UserRole.role == RoleName.ADMIN,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem convidar usuários",
        )

    valid_roles = {role.value for role in RoleName}
    if req.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role inválido. Deve ser um de: {', '.join(sorted(valid_roles))}",
        )

    role_name = RoleName(req.role)

    token = await TokenService.create_user_invitation(
        session,
        tenant_id=tenant_id,
        invited_by_id=current_user.id,
        email=req.email,
        role_name=role_name,
    )

    accept_url_base = f"{settings.FRONTEND_URL}/accept-invitation"
    send_user_invitation.delay(
        inviter_name=current_user.email,
        invitee_email=req.email,
        tenant_name="Seu Tenant",
        token=token,
        accept_url_base=accept_url_base,
    )

    return SendInvitationResponse(message="Convite enviado com sucesso")


@router.post("/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    req: AcceptInvitationRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AcceptInvitationResponse:
    """Accept invitation with token (public endpoint, unauthenticated)."""
    invitation = await TokenService.get_invitation_by_token(session, req.token)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de convite inválido ou expirado",
        )

    return AcceptInvitationResponse(
        message="Convite válido. Por favor, complete o registro.",
        tenant_id=str(invitation.tenant_id),
    )
