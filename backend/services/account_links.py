"""Single-use links for invitations and password resets.

The token travels in the URL fragment (#token=...), which browsers never send to servers or in Referer headers,
and only its SHA-256 digest is stored. Tokens expire and are deleted when used.
"""

from typing import Any, Dict

from core.config import settings
from services import mailer
from services.platform_store import get_platform_store
from services.security import new_session_token, token_digest


def issue_link(user: Dict[str, Any], purpose: str) -> Dict[str, Any]:
    """Create an invite or reset link and email it. Returns {"email_sent": bool, "link": str}."""
    token = new_session_token()
    minutes = settings.INVITE_TOKEN_HOURS * 60 if purpose == "invite" else settings.RESET_TOKEN_MINUTES
    get_platform_store().create_auth_token(token_digest(token), user["id"], purpose, minutes)
    link = f"{settings.PUBLIC_SITE_URL}/reset-password#token={token}"
    if purpose == "invite":
        subject = "You have been invited to AIDocumentAgent"
        body = (f"Hello {user['name']},\n\nAn administrator created an AIDocumentAgent account for {user['email']}.\n"
                f"Choose your password here (the link works once and expires in {settings.INVITE_TOKEN_HOURS} hours):\n\n"
                f"{link}\n\nIf you were not expecting this, you can ignore this email.\n")
    else:
        subject = "Reset your AIDocumentAgent password"
        body = (f"Hello {user['name']},\n\nSomeone asked to reset the password for {user['email']}.\n"
                f"Choose a new password here (the link works once and expires in {settings.RESET_TOKEN_MINUTES} minutes):\n\n"
                f"{link}\n\nIf this was not you, ignore this email; your password has not changed.\n")
    return {"email_sent": mailer.send_email(user["email"], subject, body), "link": link}
