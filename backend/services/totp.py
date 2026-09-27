"""Time-based one-time passwords (RFC 6238) for two-factor authentication, standard library only."""

import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from typing import List, Optional
from urllib.parse import quote

import segno

PERIOD = 30   # seconds per code
DIGITS = 6
WINDOW = 1    # accept one step either side to tolerate clock drift


def new_secret() -> str:
    """160-bit random secret, base32 (the format authenticator apps expect)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _code(secret: str, step: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10 ** DIGITS).zfill(DIGITS)


def current_step(now: Optional[float] = None) -> int:
    return int((now if now is not None else time.time()) // PERIOD)


def verify(secret: str, code: str, last_used_step: Optional[int] = None, now: Optional[float] = None) -> Optional[int]:
    """Return the matched time step, or None. Steps at or before `last_used_step` are rejected (no replay)."""
    code = "".join(ch for ch in (code or "") if ch.isdigit())
    if len(code) != DIGITS or not secret:
        return None
    step = current_step(now)
    for candidate in range(step - WINDOW, step + WINDOW + 1):
        if last_used_step is not None and candidate <= last_used_step:
            continue
        if hmac.compare_digest(_code(secret, candidate), code):
            return candidate
    return None


def provisioning_uri(secret: str, account: str, issuer: str = "AIDocumentAgent") -> str:
    return (f"otpauth://totp/{quote(issuer)}:{quote(account)}?secret={secret}&issuer={quote(issuer)}"
            f"&algorithm=SHA1&digits={DIGITS}&period={PERIOD}")


def qr_svg(uri: str) -> str:
    buffer = io.BytesIO()
    segno.make(uri, error="m").save(buffer, kind="svg", scale=5, border=2, dark="#0b1220", light="#ffffff",
                                    xmldecl=False, svgns=True)
    return buffer.getvalue().decode("utf-8")


def new_recovery_codes(count: int = 10) -> List[str]:
    """Readable single-use codes like 'k7m2-9xqp'."""
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return ["-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(2)) for _ in range(count)]


def hash_recovery_code(code: str) -> str:
    return hashlib.sha256(code.strip().lower().replace(" ", "").encode()).hexdigest()
