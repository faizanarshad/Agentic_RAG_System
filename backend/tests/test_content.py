"""Blog posts, Markdown sanitising, uploads, public visibility and settings validation."""

import io

import pytest
from PIL import Image

from conftest import ORIGIN

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '<img src=x onerror="alert(1)">',
    "[click](javascript:alert(1))",
    '<a href="javascript:alert(1)">x</a>',
    "<iframe src=https://evil.example></iframe>",
    '<svg onload="alert(1)"></svg>',
    '<div style="background:url(javascript:alert(1))">x</div>',
]


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_markdown_is_sanitised(admin_client, payload):
    html = admin_client.post("/admin/posts/preview", json={"content_md": payload}, headers=ORIGIN).json()["html"].lower()
    for bad in ("<script", "onerror", "onload", "javascript:", "<iframe", "<svg", "style="):
        assert bad not in html


def test_h1_is_reserved_for_the_title(admin_client):
    html = admin_client.post("/admin/posts/preview", json={"content_md": "# Heading"}, headers=ORIGIN).json()["html"]
    assert "<h1" not in html and "<h2>Heading</h2>" in html


def _post(client, **overrides):
    body = {"title": "A Sample Post", "content_md": "Body", "status": "draft", **overrides}
    return client.post("/admin/posts", json=body, headers=ORIGIN)


def test_visibility_of_drafts_scheduled_and_published(admin_client, anon):
    draft = _post(admin_client, title="Draft Only").json()
    future = _post(admin_client, title="Future Post", status="published", published_at="2099-01-01T00:00:00+00:00").json()
    live = _post(admin_client, title="Live Post", status="published").json()
    slugs = {p["slug"] for p in anon.get("/public/posts").json()["posts"]}
    assert live["slug"] in slugs and draft["slug"] not in slugs and future["slug"] not in slugs
    assert anon.get(f"/public/posts/{draft['slug']}").status_code == 404
    assert anon.get(f"/public/posts/{future['slug']}").status_code == 404
    public = anon.get(f"/public/posts/{live['slug']}").json()
    assert "content_md" not in public and "author_id" not in public


def test_slugs_are_unique(admin_client):
    first = _post(admin_client, title="Same Title").json()["slug"]
    second = _post(admin_client, title="Same Title").json()["slug"]
    assert first != second


def test_invalid_post_input_is_rejected(admin_client):
    assert _post(admin_client, status="hacked").status_code == 422
    assert _post(admin_client, cover_image="../../etc/passwd").status_code == 422
    assert _post(admin_client, published_at="not-a-date").status_code == 422


def _png(size=(40, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (53, 82, 242)).save(buffer, "PNG")
    return buffer.getvalue()


def test_upload_reencodes_to_webp(admin_client, anon):
    response = admin_client.post("/admin/uploads", files={"file": ("cover.png", _png(), "image/png")}, headers=ORIGIN)
    assert response.status_code == 200 and response.json()["name"].endswith(".webp")
    served = anon.get(response.json()["url"])
    assert served.status_code == 200 and served.headers["content-type"] == "image/webp"


def test_upload_rejects_non_images(admin_client):
    fake = admin_client.post("/admin/uploads", files={"file": ("x.png", b"<?php echo 1; ?>", "image/png")}, headers=ORIGIN)
    assert fake.status_code == 422


def test_uploads_cannot_escape_their_folder(anon):
    for name in ("../platform.db", "..%2Fplatform.db", "x.webp", "analytics_secret"):
        assert anon.get(f"/public/uploads/{name}").status_code == 404


def test_announcement_link_must_be_safe(admin_client):
    for url in ("javascript:alert(1)", "//evil.example", "http://insecure.example"):
        body = {"announcement": {"enabled": True, "text": "x", "link_text": "y", "link_url": url, "tone": "info"}}
        assert admin_client.put("/admin/settings", json=body, headers=ORIGIN).status_code == 422
