"""Blog posts and site settings, stored in the platform database."""

import json
import re
import sqlite3
import threading
import unicodedata
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional

import markdown
import nh3

from .platform_store import get_platform_store, iso, utcnow

DEFAULT_SETTINGS: Dict[str, Any] = {
    "announcement": {"enabled": False, "text": "", "link_text": "", "link_url": "", "tone": "info"},
    "contact_form_enabled": True,
    "analytics_enabled": True,
}

# Tags allowed in rendered post bodies (headings, lists, tables, code, images, links)
ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "em", "del", "code", "pre", "blockquote",
    "ul", "ol", "li", "a", "img", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}, "img": {"src", "alt", "title", "width", "height"},
                      "th": {"align"}, "td": {"align"}}


def render_markdown(source: str) -> str:
    """Markdown to sanitised HTML. H1 is reserved for the post title, so # headings become H2."""
    source = re.sub(r"^# ", "## ", source or "", flags=re.MULTILINE)
    html = markdown.markdown(source, extensions=["extra", "sane_lists"])
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80] or "post"


def reading_minutes(source: str) -> int:
    return max(1, round(len(re.findall(r"\w+", source or "")) / 220))


class ContentStore:
    """Posts and key/value settings in the platform SQLite database."""

    def __init__(self):
        self.db_path = get_platform_store().db_path
        self._lock = threading.Lock()
        with self._connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    slug TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    excerpt TEXT NOT NULL DEFAULT '',
                    content_md TEXT NOT NULL DEFAULT '',
                    content_html TEXT NOT NULL DEFAULT '',
                    cover_image TEXT,
                    cover_alt TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'draft',
                    seo_title TEXT,
                    seo_description TEXT,
                    reading_minutes INTEGER NOT NULL DEFAULT 1,
                    author_id TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status, published_at);
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _decode(row: sqlite3.Row) -> Dict[str, Any]:
        post = dict(row)
        post["tags"] = json.loads(post["tags"] or "[]")
        return post

    # ------------------------------------------------------------------ posts

    def unique_slug(self, base: str, exclude_id: Optional[str] = None) -> str:
        slug, n = slugify(base), 2
        candidate = slug
        with self._connect() as c:
            while c.execute("SELECT 1 FROM posts WHERE slug = ? AND id != ?", (candidate, exclude_id or "")).fetchone():
                candidate = f"{slug}-{n}"
                n += 1
        return candidate

    def save_post(self, data: Dict[str, Any], author_id: Optional[str], post_id: Optional[str] = None) -> Dict[str, Any]:
        now = iso(utcnow())
        existing = self.get_post(post_id) if post_id else None
        slug = self.unique_slug(data.get("slug") or data["title"], exclude_id=post_id)
        status = data.get("status", "draft")
        published_at = data.get("published_at") or (existing or {}).get("published_at")
        if status == "published" and not published_at:
            published_at = now
        fields = {
            "slug": slug,
            "title": data["title"].strip(),
            "excerpt": (data.get("excerpt") or "").strip(),
            "content_md": data.get("content_md") or "",
            "content_html": render_markdown(data.get("content_md") or ""),
            "cover_image": data.get("cover_image") or None,
            "cover_alt": (data.get("cover_alt") or "").strip() or None,
            "tags": json.dumps(sorted({t.strip().lower() for t in data.get("tags") or [] if t.strip()})[:8]),
            "status": status,
            "seo_title": (data.get("seo_title") or "").strip() or None,
            "seo_description": (data.get("seo_description") or "").strip() or None,
            "reading_minutes": reading_minutes(data.get("content_md") or ""),
            "published_at": published_at,
            "updated_at": now,
        }
        with self._lock, self._connect() as c:
            if existing:
                assignments = ", ".join(f"{k} = ?" for k in fields)
                c.execute(f"UPDATE posts SET {assignments} WHERE id = ?", (*fields.values(), post_id))
            else:
                post_id = str(uuid.uuid4())
                fields.update({"id": post_id, "author_id": author_id, "created_at": now})
                c.execute(
                    f"INSERT INTO posts ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                    tuple(fields.values()),
                )
        return self.get_post(post_id)

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as c:
            row = c.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return self._decode(row) if row else None

    def list_posts_admin(self) -> List[Dict[str, Any]]:
        """All posts with 30-day and all-time views from the page-view log."""
        since = iso(utcnow() - timedelta(days=30))
        with self._connect() as c:
            rows = c.execute(
                "SELECT p.id, p.slug, p.title, p.status, p.tags, p.published_at, p.updated_at, p.reading_minutes, "
                "u.name AS author_name, "
                "(SELECT COUNT(*) FROM page_views v WHERE v.path = '/blog/' || p.slug) AS views, "
                "(SELECT COUNT(*) FROM page_views v WHERE v.path = '/blog/' || p.slug AND v.created_at >= ?) AS views_30d "
                "FROM posts p LEFT JOIN users u ON u.id = p.author_id ORDER BY p.updated_at DESC",
                (since,),
            ).fetchall()
        return [self._decode(r) for r in rows]

    def list_published(self, tag: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Published posts whose publish time has passed (future dates act as scheduling)."""
        with self._connect() as c:
            rows = c.execute(
                "SELECT p.id, p.slug, p.title, p.excerpt, p.cover_image, p.cover_alt, p.tags, p.reading_minutes, "
                "p.published_at, p.updated_at, u.name AS author_name FROM posts p "
                "LEFT JOIN users u ON u.id = p.author_id "
                "WHERE p.status = 'published' AND p.published_at <= ? ORDER BY p.published_at DESC LIMIT ?",
                (iso(utcnow()), limit),
            ).fetchall()
        posts = [self._decode(r) for r in rows]
        return [p for p in posts if not tag or tag in p["tags"]]

    def get_published(self, slug: str) -> Optional[Dict[str, Any]]:
        with self._connect() as c:
            row = c.execute(
                "SELECT p.*, u.name AS author_name FROM posts p LEFT JOIN users u ON u.id = p.author_id "
                "WHERE p.slug = ? AND p.status = 'published' AND p.published_at <= ?",
                (slug, iso(utcnow())),
            ).fetchone()
        if row is None:
            return None
        post = self._decode(row)
        post.pop("content_md", None)
        post.pop("author_id", None)
        return post

    def delete_post(self, post_id: str) -> bool:
        with self._lock, self._connect() as c:
            return c.execute("DELETE FROM posts WHERE id = ?", (post_id,)).rowcount == 1

    # ------------------------------------------------------------------ settings

    def get_settings(self) -> Dict[str, Any]:
        with self._connect() as c:
            rows = c.execute("SELECT key, value FROM settings").fetchall()
        stored = {r["key"]: json.loads(r["value"]) for r in rows}
        merged = json.loads(json.dumps(DEFAULT_SETTINGS))
        for key, value in stored.items():
            if isinstance(merged.get(key), dict) and isinstance(value, dict):
                merged[key].update(value)
            elif key in merged:
                merged[key] = value
        return merged

    def update_settings(self, values: Dict[str, Any]) -> Dict[str, Any]:
        now = iso(utcnow())
        with self._lock, self._connect() as c:
            for key, value in values.items():
                if key in DEFAULT_SETTINGS:
                    c.execute(
                        "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
                        (key, json.dumps(value), now),
                    )
        return self.get_settings()


_content: Optional[ContentStore] = None
_content_lock = threading.Lock()


def get_content_store() -> ContentStore:
    global _content
    with _content_lock:
        if _content is None:
            _content = ContentStore()
    return _content
