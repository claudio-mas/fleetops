import asyncio
from abc import ABC, abstractmethod


class EmailSendError(Exception):
    """Raised when email sending fails."""
    pass


class EmailService(ABC):
    """Abstract email service — implementation can be SendGrid, Resend, SES."""

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
    ) -> None:
        """Send email. Raises EmailSendError on failure."""
        pass


class ResendEmailService(EmailService):
    """Implementation using Resend (default choice for MVP)."""

    def __init__(self, api_key: str, from_email: str, from_name: str):
        from resend import Resend  # type: ignore[attr-defined]

        self.client = Resend(api_key)
        self.from_email = from_email
        self.from_name = from_name

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
    ) -> None:
        try:
            result = await asyncio.to_thread(
                self.client.emails.send,
                {
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "text": text or html,
                },
            )
            if result.get("id") is None:
                raise EmailSendError(
                    f"Resend returned no id: {result}"
                ) from None
        except EmailSendError:
            raise
        except Exception as e:
            raise EmailSendError(
                f"Failed to send email to {to}: {e}"
            ) from e


def get_email_service() -> EmailService:
    """Factory to get configured email service."""
    from app.core.config import settings

    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not configured")

    return ResendEmailService(
        api_key=settings.RESEND_API_KEY,
        from_email=settings.EMAILS_FROM,
        from_name=settings.EMAILS_FROM_NAME,
    )
