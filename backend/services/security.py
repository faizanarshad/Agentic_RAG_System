"""Password hashing and session tokens (standard library only)."""

import hashlib
import hmac
import secrets

# PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 recommendation). scrypt would be
# preferable but is unavailable on Python builds linked against LibreSSL (e.g. macOS system Python).
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Return 'pbkdf2_sha256$iterations$salt$hash' for storage."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of a password against a stored hash."""
    try:
        parts = stored.split("$")
        if parts[0] == "pbkdf2_sha256":
            _, iterations, salt_hex, digest_hex = parts
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        elif parts[0] == "scrypt" and hasattr(hashlib, "scrypt"):
            _, n, r, p, salt_hex, digest_hex = parts
            digest = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r),
                                    p=int(p), dklen=len(digest_hex) // 2)
        else:
            return False
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


# A real hash of a random password: verifying against it costs the same as a real account,
# so response time does not reveal whether an email exists
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """Only this digest is stored, so a leaked database cannot be used to hijack sessions."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def temporary_password() -> str:
    """Readable one-time password for new users and resets (~80 bits of entropy)."""
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(3))
