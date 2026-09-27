"""Password hashing, security headers and error hygiene."""

from conftest import ORIGIN
from services.security import hash_password, temporary_password, verify_password


def test_password_hashing():
    stored = hash_password("s3cret-Password!")
    assert stored.startswith("pbkdf2_sha256$600000$")
    assert verify_password("s3cret-Password!", stored)
    assert not verify_password("wrong", stored)
    assert hash_password("same") != hash_password("same")  # unique salts


def test_temporary_passwords_are_strong():
    passwords = {temporary_password() for _ in range(50)}
    assert len(passwords) == 50 and all(len(p) == 17 for p in passwords)


def test_api_security_headers(anon):
    response = anon.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "server" not in {k.lower() for k in response.headers if response.headers[k].lower().startswith("uvicorn")}


def test_auth_responses_are_not_cached(anon):
    assert anon.get("/auth/me").headers["cache-control"] == "no-store"


def test_errors_do_not_leak_internals(anon):
    body = anon.post("/auth/login", json={"email": "x@example.com", "password": "y"}, headers=ORIGIN).text.lower()
    for leak in ("traceback", "sqlite", "select ", "pbkdf2"):
        assert leak not in body
