"""Sign-in, sign-out, current user, password change and session management."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from core.config import settings
from services.platform_store import get_platform_store
from services.security import DUMMY_HASH, hash_password, new_session_token, token_digest, verify_password
from utils.logger import logger
from .deps import client_ip, public_user, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def validate_new_password(password: str, email: str = "") -> None:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=422, detail=f"Use at least {settings.PASSWORD_MIN_LENGTH} characters.")
    if len(password) > 256:
        raise HTTPException(status_code=422, detail="Password is too long.")
    if email and password.lower() == email.lower():
        raise HTTPException(status_code=422, detail="Password must not be your email address.")


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response) -> Dict[str, Any]:
    store = get_platform_store()
    email, ip = payload.email.strip().lower(), client_ip(request)

    failures = store.recent_failures(email, ip, settings.LOGIN_LOCKOUT_MINUTES)
    if failures["email"] >= settings.LOGIN_MAX_ATTEMPTS or failures["ip"] >= settings.LOGIN_MAX_ATTEMPTS * 4:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {settings.LOGIN_LOCKOUT_MINUTES} minutes.",
        )

    user = store.get_user_by_email(email)
    # Always run a hash comparison so timing does not reveal whether the account exists
    valid = verify_password(payload.password, user["password_hash"] if user else DUMMY_HASH)
    if not user or not valid or user["status"] != "active":
        store.record_login_attempt(email, ip, False)
        store.log_event("auth.login_failed", user["id"] if user else None, "auth", {"email": email}, ip)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    store.record_login_attempt(email, ip, True)
    token = new_session_token()
    store.create_session(token_digest(token), user["id"], ip, request.headers.get("user-agent", ""))
    store.purge_expired_sessions()
    store.log_event("auth.login", user["id"], "auth", None, ip)
    _set_session_cookie(response, token)
    logger.info(f"User signed in: {email}")
    return {"user": public_user(store.get_user(user["id"]))}


@router.post("/logout")
def logout(request: Request, response: Response) -> Dict[str, bool]:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        store = get_platform_store()
        user = store.get_session_user(token_digest(token))
        store.delete_session(token_digest(token))
        if user:
            store.log_event("auth.logout", user["id"], "auth", None, client_ip(request))
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    return {"user": public_user(user)}


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, request: Request,
                    user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    store = get_platform_store()
    if not verify_password(payload.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    validate_new_password(payload.new_password, user["email"])
    if verify_password(payload.new_password, user["password_hash"]):
        raise HTTPException(status_code=422, detail="Choose a password different from the current one.")
    store.update_user(user["id"], password_hash=hash_password(payload.new_password), must_change_password=0)
    # Changing a password signs out every other device
    signed_out = store.delete_user_sessions(user["id"], except_token_hash=request.state.session_digest)
    store.log_event("auth.password_changed", user["id"], "auth", {"other_sessions_signed_out": signed_out},
                    client_ip(request))
    return {"ok": True, "other_sessions_signed_out": signed_out}


@router.get("/sessions")
def sessions(request: Request, user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    current = request.state.session_digest
    items = []
    for s in get_platform_store().list_user_sessions(user["id"]):
        items.append({
            "current": s["token_hash"] == current,
            "created_at": s["created_at"],
            "last_seen_at": s["last_seen_at"],
            "expires_at": s["expires_at"],
            "ip": s["ip"],
            "user_agent": s["user_agent"],
        })
    return {"sessions": items}


@router.post("/sessions/revoke-others")
def revoke_other_sessions(request: Request, user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    count = get_platform_store().delete_user_sessions(user["id"], except_token_hash=request.state.session_digest)
    get_platform_store().log_event("auth.sessions_revoked", user["id"], "auth", {"count": count}, client_ip(request))
    return {"ok": True, "signed_out": count}
