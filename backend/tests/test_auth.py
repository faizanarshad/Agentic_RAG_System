"""Sign-in, sessions, password changes and brute-force protection."""

from conftest import ORIGIN, PASSWORD, login, make_user
from services.security import token_digest


def test_login_sets_httponly_samesite_cookie(anon):
    make_user("cookie@example.com")
    response = anon.post("/auth/login", json={"email": "cookie@example.com", "password": PASSWORD}, headers=ORIGIN)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "ada_session=" in cookie and "httponly" in cookie and "samesite=lax" in cookie


def test_wrong_password_and_unknown_email_get_identical_errors(anon):
    make_user("enum@example.com")
    wrong = anon.post("/auth/login", json={"email": "enum@example.com", "password": "nope-nope-nope"}, headers=ORIGIN)
    unknown = anon.post("/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"}, headers=ORIGIN)
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()  # no account enumeration


def test_lockout_after_repeated_failures(anon):
    make_user("lock@example.com")
    for _ in range(5):
        anon.post("/auth/login", json={"email": "lock@example.com", "password": "wrong-password-x"}, headers=ORIGIN)
    blocked = anon.post("/auth/login", json={"email": "lock@example.com", "password": PASSWORD}, headers=ORIGIN)
    assert blocked.status_code == 429  # even the right password is refused while locked


def test_disabled_user_cannot_sign_in(anon, store):
    user = make_user("disabled@example.com")
    store.update_user(user["id"], status="disabled")
    response = anon.post("/auth/login", json={"email": "disabled@example.com", "password": PASSWORD}, headers=ORIGIN)
    assert response.status_code == 401


def test_session_token_is_stored_only_as_digest(anon, store):
    make_user("digest@example.com")
    client = login("digest@example.com")
    token = client.cookies.get("ada_session")
    rows = store.query("SELECT token_hash FROM sessions")
    assert all(r["token_hash"] != token for r in rows)
    assert any(r["token_hash"] == token_digest(token) for r in rows)


def test_logout_invalidates_session():
    make_user("logout@example.com")
    client = login("logout@example.com")
    assert client.get("/auth/me").status_code == 200
    client.post("/auth/logout", headers=ORIGIN)
    client.cookies.clear()
    assert client.get("/auth/me").status_code == 401


def test_change_password_rules_and_signs_out_other_sessions():
    make_user("change@example.com")
    first, second = login("change@example.com"), login("change@example.com")
    bad = [
        ({"current_password": "wrong", "new_password": "Another-Password-1"}, 400),
        ({"current_password": PASSWORD, "new_password": "short"}, 422),
        ({"current_password": PASSWORD, "new_password": PASSWORD}, 422),
        ({"current_password": PASSWORD, "new_password": "change@example.com"}, 422),
    ]
    for body, status in bad:
        assert first.post("/auth/change-password", json=body, headers=ORIGIN).status_code == status
    ok = first.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": "Brand-New-Pass-42"}, headers=ORIGIN)
    assert ok.status_code == 200 and ok.json()["other_sessions_signed_out"] == 1
    assert first.get("/auth/me").status_code == 200
    assert second.get("/auth/me").status_code == 401


def test_temporary_password_flag_is_cleared_after_change():
    make_user("temp@example.com", must_change=True)
    client = login("temp@example.com")
    assert client.get("/auth/me").json()["user"]["must_change_password"] is True
    client.post("/auth/change-password", json={"current_password": PASSWORD, "new_password": "Brand-New-Pass-42"}, headers=ORIGIN)
    assert client.get("/auth/me").json()["user"]["must_change_password"] is False
