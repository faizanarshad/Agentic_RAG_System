"""Contact form validation, spam controls, and privacy of website analytics."""

from conftest import ORIGIN

VALID = {"name": "Sam Test", "email": "sam@example.com", "message": "A sufficiently long enquiry message.", "consent": True}


def test_contact_validation(anon):
    assert anon.post("/contact", json={**VALID, "email": "not-an-email"}, headers=ORIGIN).status_code == 422
    assert anon.post("/contact", json={**VALID, "message": "short"}, headers=ORIGIN).status_code == 422
    assert anon.post("/contact", json={**VALID, "consent": False}, headers=ORIGIN).status_code == 422
    assert anon.post("/contact", json=VALID, headers=ORIGIN).status_code == 200


def test_honeypot_is_accepted_silently_but_not_stored(anon, admin_client):
    before = admin_client.get("/admin/messages").json()["total"]
    assert anon.post("/contact", json={**VALID, "website": "http://spam"}, headers=ORIGIN).status_code == 200
    assert admin_client.get("/admin/messages").json()["total"] == before


def test_contact_rate_limit(anon):
    statuses = [anon.post("/contact", json=VALID, headers=ORIGIN).status_code for _ in range(6)]
    assert statuses[:5] == [200] * 5 and statuses[5] == 429


def test_contact_form_can_be_paused(anon, admin_client):
    admin_client.put("/admin/settings", json={"contact_form_enabled": False}, headers=ORIGIN)
    try:
        assert anon.post("/contact", json=VALID, headers=ORIGIN).status_code == 503
    finally:
        admin_client.put("/admin/settings", json={"contact_form_enabled": True}, headers=ORIGIN)


def _view(client, path, ua="Mozilla/5.0 (Macintosh) Chrome/140", referrer=""):
    return client.post("/analytics/pageview", content=f'{{"path":"{path}","referrer":"{referrer}"}}',
                       headers={"Content-Type": "text/plain", "User-Agent": ua, **ORIGIN})


def test_pageviews_skip_bots_and_private_areas(anon, store):
    before = store.scalar("SELECT COUNT(*) FROM page_views")
    for path in ("/workspace", "/admin/users", "/login", "not-a-path"):
        assert _view(anon, path).status_code == 204
    assert _view(anon, "/about", ua="Googlebot/2.1").status_code == 204
    assert _view(anon, "/about", ua="Chrome-Lighthouse").status_code == 204
    assert store.scalar("SELECT COUNT(*) FROM page_views") == before


def test_pageviews_store_no_ip_and_drop_own_referrer(anon, store):
    _view(anon, "/about", referrer="http://localhost:3001/")
    _view(anon, "/about", referrer="https://news.example.com/article?id=1")
    rows = store.query("SELECT visitor, referrer FROM page_views ORDER BY id DESC LIMIT 2")
    assert rows[0]["referrer"] == "news.example.com" and rows[1]["referrer"] is None
    assert all("testclient" not in r["visitor"] and len(r["visitor"]) == 16 for r in rows)


def test_csv_export_neutralises_formulas(anon, admin_client):
    anon.post("/contact", json={**VALID, "name": "=HYPERLINK(\"http://evil\")"}, headers=ORIGIN)
    csv_text = admin_client.get("/admin/messages.csv").text
    assert "'=HYPERLINK" in csv_text and ",=HYPERLINK" not in csv_text
