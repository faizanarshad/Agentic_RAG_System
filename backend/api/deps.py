"""Authentication dependencies shared by the API routers."""

from typing import Any, Dict

from fastapi import HTTPException, Request

from core.config import settings
from services.platform_store import get_platform_store
from services.security import token_digest
from services.usage_tracker import current_user_id


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "must_change_password": bool(user["must_change_password"]),
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
