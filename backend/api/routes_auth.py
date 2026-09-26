"""Sign-in, sign-out, current user, password change and session management."""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from core.config import settings
from services.platform_store import get_platform_store
from services import totp
from services.security import DUMMY_HASH, hash_password, new_session_token, token_digest, verify_password
from utils.logger import logger
from .deps import client_ip, public_user, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class MfaLoginRequest(BaseModel):
    mfa_token: str
    code: str


class CodeRequest(BaseModel):
    code: str


class DisableTotpRequest(BaseModel):
    password: str
    code: str


class PasswordRequest(BaseModel):
    password: str


MFA_MAX_ATTEMPTS = 5


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

    if user.get("totp_enabled"):
        # Password is correct, but no session until the second factor is verified
        challenge = new_session_token()
        store.create_mfa_challenge(token_digest(challenge), user["id"])
        store.log_event("auth.mfa_challenge", user["id"], "auth", None, ip)
        return {"mfa_required": True, "mfa_token": challenge}

    store.record_login_attempt(email, ip, True)
    _start_session(request, response, user, ip, method="password")
    return {"user": public_user(store.get_user(user["id"]))}


def _start_session(request: Request, response: Response, user: Dict[str, Any], ip: str, method: str) -> None:
    store = get_platform_store()
    token = new_session_token()
    store.create_session(token_digest(token), user["id"], ip, request.headers.get("user-agent", ""))
    store.purge_expired_sessions()
    store.log_event("auth.login", user["id"], "auth", {"method": method}, ip)
    _set_session_cookie(response, token)
    logger.info(f"User signed in: {user['email']} ({method})")


def _check_second_factor(user: Dict[str, Any], code: str) -> Optional[str]:
    """Verify a TOTP code or a recovery code; consumes it. Returns 'totp', 'recovery' or None."""
    store = get_platform_store()
    step = totp.verify(user.get("totp_secret") or "", code, user.get("totp_last_step"))
    if step is not None:
        store.update_user(user["id"], totp_last_step=step)
        return "totp"
    hashes = json.loads(user.get("recovery_codes") or "[]")
    digest = totp.hash_recovery_code(code)
    if digest in hashes:
        hashes.remove(digest)
        store.update_user(user["id"], recovery_codes=json.dumps(hashes))
        return "recovery"
    return None


@router.post("/login/mfa")
def login_mfa(payload: MfaLoginRequest, request: Request, response: Response) -> Dict[str, Any]:
    """Second sign-in step: a 6-digit authenticator code or a single-use recovery code."""
    store = get_platform_store()
    ip = client_ip(request)
    digest = token_digest(payload.mfa_token)
    challenge = store.get_mfa_challenge(digest)
    if challenge is None:
        raise HTTPException(status_code=401, detail="This sign-in attempt has expired. Please sign in again.")
    if challenge["attempts"] >= MFA_MAX_ATTEMPTS:
        store.delete_mfa_challenge(digest)
        raise HTTPException(status_code=429, detail="Too many incorrect codes. Please sign in again.")
    user = store.get_user(challenge["user_id"])
    if user is None or user["status"] != "active" or not user.get("totp_enabled"):
        store.delete_mfa_challenge(digest)
        raise HTTPException(status_code=401, detail="Please sign in again.")
    method = _check_second_factor(user, payload.code)
    if method is None:
        store.bump_mfa_attempts(digest)
        store.record_login_attempt(user["email"], ip, False)
        store.log_event("auth.mfa_failed", user["id"], "auth", None, ip)
        raise HTTPException(status_code=401, detail="That code is not valid.")
    store.delete_mfa_challenge(digest)
    store.record_login_attempt(user["email"], ip, True)
    _start_session(request, response, user, ip, method=method)
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


# ---------------------------------------------------------------------- two-factor authentication

@router.post("/2fa/setup")
def totp_setup(request: Request, user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    """Start enrolment: a new secret is stored as pending until a valid code confirms it."""
    if user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="Two-factor authentication is already on.")
    secret = totp.new_secret()
    get_platform_store().update_user(user["id"], totp_pending_secret=secret)
    uri = totp.provisioning_uri(secret, user["email"])
    return {"secret": secret, "otpauth_uri": uri, "qr_svg": totp.qr_svg(uri)}


@router.post("/2fa/enable")
def totp_enable(payload: CodeRequest, request: Request, user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    pending = user.get("totp_pending_secret")
    if not pending:
        raise HTTPException(status_code=400, detail="Start set-up first.")
    step = totp.verify(pending, payload.code)
    if step is None:
        raise HTTPException(status_code=400, detail="That code is not valid. Check the time on your phone and try again.")
    codes = totp.new_recovery_codes()
    get_platform_store().update_user(
        user["id"], totp_secret=pending, totp_pending_secret=None, totp_enabled=1, totp_last_step=step,
        recovery_codes=json.dumps([totp.hash_recovery_code(c) for c in codes]),
    )
    get_platform_store().log_event("auth.2fa_enabled", user["id"], "auth", None, client_ip(request))
    # Recovery codes are shown once and stored only as hashes
    return {"ok": True, "recovery_codes": codes}


@router.post("/2fa/disable")
def totp_disable(payload: DisableTotpRequest, request: Request,
                 user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    if not user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="Two-factor authentication is not on.")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Your password is incorrect.")
    if _check_second_factor(user, payload.code) is None:
        raise HTTPException(status_code=400, detail="That code is not valid.")
    get_platform_store().update_user(user["id"], totp_secret=None, totp_pending_secret=None, totp_enabled=0,
                                     totp_last_step=None, recovery_codes=None)
    get_platform_store().log_event("auth.2fa_disabled", user["id"], "auth", None, client_ip(request))
    return {"ok": True}


@router.post("/2fa/recovery-codes")
def regenerate_recovery_codes(payload: PasswordRequest, request: Request,
                              user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    if not user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="Turn on two-factor authentication first.")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Your password is incorrect.")
    codes = totp.new_recovery_codes()
    get_platform_store().update_user(user["id"], recovery_codes=json.dumps([totp.hash_recovery_code(c) for c in codes]))
    get_platform_store().log_event("auth.recovery_codes_regenerated", user["id"], "auth", None, client_ip(request))
    return {"recovery_codes": codes}
