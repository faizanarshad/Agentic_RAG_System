"""Authorisation, CSRF origin guard, CORS and admin safeguards."""

import pytest

from conftest import ORIGIN, login, make_user

WORKSPACE_ENDPOINTS = [
    ("get", "/legal/documents"), ("get", "/legal/corpus/stats"), ("get", "/engineering/drawings"),
    ("get", "/engineering/templates"), ("get", "/files/health"), ("post", "/chat/"),
]
ADMIN_ENDPOINTS = [
    ("get", "/admin/overview"), ("get", "/admin/users"), ("get", "/admin/messages"), ("get", "/admin/activity"),
    ("get", "/admin/posts"), ("get", "/admin/settings"), ("get", "/admin/usage"), ("get", "/admin/traffic"),
    ("get", "/admin/realtime"), ("get", "/admin/activity.csv"),
]


@pytest.mark.parametrize("method,path", WORKSPACE_ENDPOINTS + ADMIN_ENDPOINTS)
def test_anonymous_requests_are_rejected(anon, method, path):
    assert getattr(anon, method)(path, headers=ORIGIN).status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
def test_members_cannot_reach_admin(member_client, method, path):
    assert getattr(member_client, method)(path).status_code == 403


def test_members_can_use_workspaces(member_client):
    assert member_client.get("/engineering/templates").status_code == 200


def test_admin_can_reach_admin(admin_client):
    assert admin_client.get("/admin/overview").status_code == 200


def test_foreign_origin_is_blocked_on_state_changing_requests(admin_client):
    evil = admin_client.post("/admin/users", json={"email": "x@example.com", "name": "X"}, headers={"Origin": "https://evil.example"})
    assert evil.status_code == 403


def test_cors_allows_only_configured_origin(anon):
    allowed = anon.options("/auth/login", headers={**ORIGIN, "Access-Control-Request-Method": "POST"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3001"
    assert allowed.headers.get("access-control-allow-credentials") == "true"
    other = anon.options("/auth/login", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert other.headers.get("access-control-allow-origin") is None


def test_user_management_and_safeguards(admin_client, store):
    created = admin_client.post("/admin/users", json={"email": "invitee@example.com", "name": "Invitee"}, headers=ORIGIN)
    body = created.json()
    assert created.status_code == 200 and "temporary_password" not in body
    assert body["email_sent"] is False and "/reset-password#token=" in body["link"]  # SMTP is not configured in tests
    assert admin_client.post("/admin/users", json={"email": "invitee@example.com", "name": "Again"}, headers=ORIGIN).status_code == 409
    me = admin_client.get("/auth/me").json()["user"]
    assert admin_client.delete(f"/admin/users/{me['id']}", headers=ORIGIN).status_code == 400


def test_last_admin_cannot_be_removed(store):
    for u in store.list_users():
        if u["role"] == "admin":
            store.update_user(u["id"], role="member")
    admin = make_user("only-admin@example.com", "admin")
    client = login("only-admin@example.com")
    response = client.patch(f"/admin/users/{admin['id']}", json={"role": "member"}, headers=ORIGIN)
    assert response.status_code == 400


def test_disabling_a_user_signs_them_out(admin_client):
    target = make_user("to-disable@example.com")
    victim = login("to-disable@example.com")
    admin_client.patch(f"/admin/users/{target['id']}", json={"status": "disabled"}, headers=ORIGIN)
    assert victim.get("/auth/me").status_code == 401
