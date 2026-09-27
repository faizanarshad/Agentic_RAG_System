"""Invitations and password resets use single-use, expiring links; responses never reveal whether an account exists."""

from services import account_links, mailer
from conftest import ORIGIN, PASSWORD, login, make_user

NEW_PASSWORD = "Another-Strong-Pass-42"


def _token(link: str) -> str:
    return link.split("#token=", 1)[1]


def test_invited_user_sets_their_own_password(admin_client, anon, store):
    email = "invite-flow@example.com"
    existing = store.get_user_by_email(email)
    if existing:
        store.delete_user(existing["id"])
    link = admin_client.post("/admin/users", json={"email": email, "name": "Invited"}, headers=ORIGIN).json()["link"]
    token = _token(link)

    check = anon.post("/auth/reset-password/check", json={"token": token}, headers=ORIGIN).json()
    assert check == {"valid": True, "purpose": "invite", "email": email}
    # A weak password is rejected without using up the link
    assert anon.post("/auth/reset-password", json={"token": token, "password": "short"}, headers=ORIGIN).status_code == 422
    assert anon.post("/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN).status_code == 200
    # Single use
    assert anon.post("/auth/reset-password", json={"token": token, "password": NEW_PASSWORD}, headers=ORIGIN).status_code == 400
    assert anon.post("/auth/reset-password/check", json={"token": token}, headers=ORIGIN).json() == {"valid": False}
    login(email, NEW_PASSWORD)


def test_forgot_password_does_not_reveal_accounts(anon, monkeypatch):
    sent = []
    monkeypatch.setattr(account_links, "issue_link", lambda user, purpose: sent.append(user["email"]))
    from api import routes_auth
    monkeypatch.setattr(routes_auth, "issue_link", lambda user, purpose: sent.append(user["email"]))
    make_user("forgot-real@example.com")
    real = anon.post("/auth/forgot-password", json={"email": "forgot-real@example.com"}, headers=ORIGIN)
    fake = anon.post("/auth/forgot-password", json={"email": "nobody-here@example.com"}, headers=ORIGIN)
    assert real.status_code == fake.status_code == 200 and real.json() == fake.json()
    assert sent == ["forgot-real@example.com"]


def test_forgot_password_is_rate_limited(anon):
    responses = [anon.post("/auth/forgot-password", json={"email": "limit@example.com"}, headers=ORIGIN).status_code
                 for _ in range(4)]
    assert responses[-1] == 429


def test_reset_signs_out_sessions_and_replaces_password(store, anon):
    user = make_user("reset-flow@example.com")
    client = login("reset-flow@example.com")
    link = account_links.issue_link(user, "reset")["link"]
    assert anon.post("/auth/reset-password", json={"token": _token(link), "password": NEW_PASSWORD},
                     headers=ORIGIN).status_code == 200
    assert client.get("/auth/me").status_code == 401
    assert anon.post("/auth/login", json={"email": "reset-flow@example.com", "password": PASSWORD},
                     headers=ORIGIN).status_code == 401
    login("reset-flow@example.com", NEW_PASSWORD)


def test_expired_and_forged_tokens_are_rejected(store, anon):
    user = make_user("expired@example.com")
    link = account_links.issue_link(user, "reset")["link"]
    store.query("UPDATE auth_tokens SET expires_at = '2000-01-01T00:00:00+00:00' WHERE user_id = ?", (user["id"],))
    for token in (_token(link), "forged-token"):
        assert anon.post("/auth/reset-password", json={"token": token, "password": NEW_PASSWORD},
                         headers=ORIGIN).status_code == 400


def test_tokens_are_stored_only_as_digests(store):
    user = make_user("digest@example.com")
    token = _token(account_links.issue_link(user, "reset")["link"])
    rows = store.query("SELECT token_hash FROM auth_tokens WHERE user_id = ?", (user["id"],))
    assert rows and rows[0]["token_hash"] != token and len(rows[0]["token_hash"]) == 64


def test_admin_reset_disables_old_password(admin_client, anon, store):
    user = make_user("admin-reset@example.com")
    body = admin_client.post(f"/admin/users/{user['id']}/reset-password", json={}, headers=ORIGIN).json()
    assert body["email_sent"] is False and body["link"]
    assert anon.post("/auth/login", json={"email": "admin-reset@example.com", "password": PASSWORD},
                     headers=ORIGIN).status_code == 401


def test_mailer_reports_unconfigured():
    assert mailer.is_configured() is False
    assert mailer.send_email("x@example.com", "s", "b") is False
