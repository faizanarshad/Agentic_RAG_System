"""Outgoing email (invitations and password resets) over SMTP with STARTTLS or implicit TLS."""

import smtplib
import ssl
from email.message import EmailMessage

from core.config import settings
from utils.logger import logger


def is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns False (and logs why) if SMTP is not configured or sending fails."""
    if not is_configured():
        logger.warning("Email not sent: SMTP_HOST and SMTP_FROM are not configured")
        return False
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=20)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            server.starttls(context=context)  # never send credentials or links in clear text
        with server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as e:
        logger.error(f"Email to {to} failed: {e.__class__.__name__}: {e}")
        return False
