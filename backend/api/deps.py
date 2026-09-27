"""Authentication dependencies shared by the API routers."""

import json
from typing import Any, Dict

from fastapi import HTTPException, Request

from core.config import settings
from services.platform_store import get_platform_store
from services.security import token_digest
from services.usage_tracker import current_user_id


def client_ip(request: Request) -> str:
    """The real client IP. X-Forwarded-For is honoured only when the direct peer is a trusted proxy,
    taking the right-most address that is not itself a trusted proxy, so the header cannot be spoofed."""
    peer = request.client.host if request.client else "unknown"
    if peer not in settings.TRUSTED_PROXIES:
        return peer
    forwarded = [ip.strip() for ip in request.headers.get("x-forwarded-for", "").split(",") if ip.strip()]
    for ip in reversed(forwarded):
        if ip not in settings.TRUSTED_PROXIES:
            return ip[:64]
    return peer


def public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "must_change_password": bool(user["must_change_password"]),
        "totp_enabled": bool(user.get("totp_enabled")),
        "recovery_codes_left": len(json.loads(user["recovery_codes"])) if user.get("recovery_codes") else 0,
    }


def get_session_user(request: Request):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None, None
    digest = token_digest(token)
    return get_platform_store().get_session_user(digest), digest


async def require_user(request: Request) -> Dict[str, Any]:
    """Reject the request unless it carries a valid session for an active user.

    Async on purpose: it runs in the request's own context, so `current_user_id` set here is
    inherited by the (threadpool) endpoint and attributed to model-usage records.
    """
    user, digest = get_session_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    request.state.user = user
    request.state.session_digest = digest
    current_user_id.set(user["id"])
    return user


async def require_admin(request: Request) -> Dict[str, Any]:
    user = await require_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user


def owner_scope(request: Request):
    """The owner filter for workspace data: None for administrators (they see everything),
    otherwise the signed-in member's user ID, so members only ever see their own records."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return None if user["role"] == "admin" else user["id"]


def current_owner_id(request: Request) -> str:
    """The signed-in user's ID, recorded as the owner of anything they create."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return user["id"]


def can_access(record, scope) -> bool:
    """True when a record exists and falls inside the caller's owner scope."""
    return record is not None and (scope is None or record.get("owner_id") == scope)
