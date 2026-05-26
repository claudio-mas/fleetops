import asyncio
import logging
from typing import Any

from celery import shared_task  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def send_email_verification(
    self: Any,
    user_id: str,
    tenant_id: str,
    email: str,
    token: str,
    verify_url_base: str,
) -> None:
    """Send email verification email asynchronously."""
    from app.services.email_service import EmailSendError, get_email_service

    try:
        service = get_email_service()
        verify_link = f"{verify_url_base}/{token}"

        html = f"""
        <h2>Bem-vindo ao FleetOps!</h2>
        <p>Clique no link abaixo para confirmar seu e-mail:</p>
        <a href="{verify_link}">Confirmar E-mail</a>
        <p>Link expira em 24 horas.</p>
        """

        asyncio.run(
            service.send_email(
                to=email,
                subject="Confirme seu e-mail no FleetOps",
                html=html,
            )
        )
        logger.info(f"Email verification sent to {email}")
    except EmailSendError as e:
        logger.error(f"Failed to send verification email: {e}")
        raise self.retry(exc=e) from e


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def send_user_invitation(
    self: Any,
    inviter_name: str,
    invitee_email: str,
    tenant_name: str,
    token: str,
    accept_url_base: str,
) -> None:
    """Send user invitation email asynchronously."""
    from app.services.email_service import EmailSendError, get_email_service

    try:
        service = get_email_service()
        accept_link = f"{accept_url_base}/{token}"

        html = f"""
        <h2>{inviter_name} convida você a {tenant_name}</h2>
        <p>Clique no link abaixo para aceitar o convite:</p>
        <a href="{accept_link}">Aceitar Convite</a>
        <p>Link expira em 7 dias.</p>
        """

        asyncio.run(
            service.send_email(
                to=invitee_email,
                subject=f"Convite para {tenant_name} no FleetOps",
                html=html,
            )
        )
        logger.info(f"Invitation sent to {invitee_email}")
    except EmailSendError as e:
        logger.error(f"Failed to send invitation email: {e}")
        raise self.retry(exc=e) from e
