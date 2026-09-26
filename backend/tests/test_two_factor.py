"""Two-factor authentication (TOTP + recovery codes)."""

import base64
import time

from conftest import ORIGIN, PASSWORD, login, make_user
from services import totp


def enable_2fa(client):
    setup = client.post("/auth/2fa/setup", headers=ORIGIN).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/") and setup["qr_svg"].startswith("<svg")
    code = totp._code(setup["secret"], totp.current_step())
    enabled = client.post("/auth/2fa/enable", json={"code": code}, headers=ORIGIN)
    assert enabled.status_code == 200
    return setup["secret"], enabled.json()["recovery_codes"]


def test_rfc4226_vectors():
    secret = base64.b32encode(b"12345678901234567890").decode().rstrip("=")
    expected = ["755224", "287082", "359152", "969429", "338314", "254676", "287922", "162583", "399871", "520489"]
    assert [totp._code(secret, i) for i in range(10)] == expected


def test_enable_requires_valid_code():
    make_user("mfa-invalid@example.com")
    client = login("mfa-invalid@example.com")
    client.post("/auth/2fa/setup", headers=ORIGIN)
    assert client.post("/auth/2fa/enable", json={"code": "000000"}, headers=ORIGIN).status_code == 400


def test_login_requires_second_factor_and_codes_cannot_be_replayed(anon):
    make_user("mfa@example.com")
    secret, _ = enable_2fa(login("mfa@example.com"))
    first = anon.post("/auth/login", json={"email": "mfa@example.com", "password": PASSWORD}, headers=ORIGIN)
    assert first.status_code == 200 and first.json()["mfa_required"] is True
    assert "set-cookie" not in first.headers  # no session before the second factor
    # The code used during enrolment was for this time step, so wait for a fresh one if needed
    step = totp.current_step()
    code = totp._code(secret, step + 1)
    ok = anon.post("/auth/login/mfa", json={"mfa_token": first.json()["mfa_token"], "code": code}, headers=ORIGIN)
    assert ok.status_code == 200 and "ada_session=" in ok.headers["set-cookie"]
    again = anon.post("/auth/login", json={"email": "mfa@example.com", "password": PASSWORD}, headers=ORIGIN).json()
    replay = anon.post("/auth/login/mfa", json={"mfa_token": again["mfa_token"], "code": code}, headers=ORIGIN)
    assert replay.status_code == 401


def test_recovery_code_works_once(anon):
    make_user("mfa-recovery@example.com")
    _, codes = enable_2fa(login("mfa-recovery@example.com"))
    for expected in (200, 401):
        challenge = anon.post("/auth/login", json={"email": "mfa-recovery@example.com", "password": PASSWORD}, headers=ORIGIN).json()
        response = anon.post("/auth/login/mfa", json={"mfa_token": challenge["mfa_token"], "code": codes[0]}, headers=ORIGIN)
        assert response.status_code == expected


def test_challenge_locks_after_five_wrong_codes(anon):
    make_user("mfa-brute@example.com")
    enable_2fa(login("mfa-brute@example.com"))
    challenge = anon.post("/auth/login", json={"email": "mfa-brute@example.com", "password": PASSWORD}, headers=ORIGIN).json()
    statuses = [anon.post("/auth/login/mfa", json={"mfa_token": challenge["mfa_token"], "code": "123456"}, headers=ORIGIN).status_code
                for _ in range(6)]
    assert statuses[:5] == [401] * 5 and statuses[5] == 429


def test_disable_requires_password_and_code():
    make_user("mfa-off@example.com")
    client = login("mfa-off@example.com")
    secret, codes = enable_2fa(client)
    assert client.post("/auth/2fa/disable", json={"password": "wrong", "code": codes[1]}, headers=ORIGIN).status_code == 400
    assert client.post("/auth/2fa/disable", json={"password": PASSWORD, "code": "000000"}, headers=ORIGIN).status_code == 400
    assert client.post("/auth/2fa/disable", json={"password": PASSWORD, "code": codes[1]}, headers=ORIGIN).status_code == 200
    assert client.get("/auth/me").json()["user"]["totp_enabled"] is False


def test_admin_can_reset_a_users_2fa(admin_client, store):
    user = make_user("mfa-lost@example.com")
    enable_2fa(login("mfa-lost@example.com"))
    assert admin_client.post(f"/admin/users/{user['id']}/reset-2fa", headers=ORIGIN).status_code == 200
    assert not store.get_user(user["id"])["totp_enabled"]


def test_recovery_codes_are_stored_hashed(store):
    user = make_user("mfa-hash@example.com")
    _, codes = enable_2fa(login("mfa-hash@example.com"))
    stored = store.get_user(user["id"])["recovery_codes"]
    assert all(code not in stored for code in codes)
