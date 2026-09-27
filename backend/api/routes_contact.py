"""Contact form endpoint for the public website."""

import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from utils.logger import logger

router = APIRouter(prefix="/contact", tags=["contact"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contact")
DB_PATH = os.path.join(DATA_DIR, "messages.db")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
TOPICS = {"engineering", "legal", "medical", "pilot", "integration", "other"}
RATE_LIMIT = 5            # messages
RATE_WINDOW_SECONDS = 3600  # per hour per client IP



def _connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            topic TEXT,
            message TEXT NOT NULL,
            client_ip TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    # Migration: read status for the admin inbox
    columns = {row[1] for row in connection.execute("PRAGMA table_info(messages)")}
    if "read_at" not in columns:
        connection.execute("ALTER TABLE messages ADD COLUMN read_at TEXT")
    return connection


class ContactMessage(BaseModel):
    """A message submitted from the website contact form."""
    name: str
    email: str
    company: str = ""
    topic: str = "other"
    message: str
    consent: bool = False
    website: str = ""  # honeypot: real visitors never fill this in


@router.post("")
def submit_contact(payload: ContactMessage, request: Request) -> Dict[str, bool]:
    """Validate and store a contact message."""
    from services.content_store import get_content_store
    if not get_content_store().get_settings()["contact_form_enabled"]:
        raise HTTPException(status_code=503, detail="The contact form is temporarily unavailable.")

    # Silently accept honeypot submissions so bots get no signal
    if payload.website.strip():
        logger.info("Contact form honeypot triggered; message discarded")
        return {"ok": True}

    name, email, message = payload.name.strip(), payload.email.strip(), payload.message.strip()
    if not 2 <= len(name) <= 120:
        raise HTTPException(status_code=422, detail="Please enter your name.")
    if not EMAIL_PATTERN.match(email) or len(email) > 254:
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")
    if not 20 <= len(message) <= 5000:
        raise HTTPException(status_code=422, detail="Messages must be between 20 and 5,000 characters.")
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Consent is required so we can reply.")

    from api.deps import client_ip as resolve_ip
    from services.platform_store import get_platform_store as _store
    client_ip = resolve_ip(request)
    if _store().rate_limited("contact", client_ip, RATE_LIMIT, RATE_WINDOW_SECONDS):
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later.")

    with _connect() as connection:
        connection.execute(
            "INSERT INTO messages (name, email, company, topic, message, client_ip, user_agent, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                email,
                payload.company.strip()[:200],
                payload.topic if payload.topic in TOPICS else "other",
                message,
                client_ip,
                request.headers.get("user-agent", "")[:300],
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
    logger.info(f"Contact message stored (topic: {payload.topic})")
    from services.platform_store import get_platform_store
    get_platform_store().log_event("contact.message", None, "website", {"topic": payload.topic}, client_ip)
    return {"ok": True}


# ---------------------------------------------------------------------- admin inbox helpers

def list_messages(status: str = "all", limit: int = 200, offset: int = 0):
    where = {"unread": "WHERE read_at IS NULL", "read": "WHERE read_at IS NOT NULL"}.get(status, "")
    with _connect() as connection:
        connection.row_factory = sqlite3.Row
        total = connection.execute(f"SELECT COUNT(*) FROM messages {where}").fetchone()[0]
        rows = connection.execute(
            f"SELECT id, name, email, company, topic, message, created_at, read_at FROM messages {where} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return {"total": total, "messages": [dict(r) for r in rows]}


def message_stats():
    with _connect() as connection:
        total = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        unread = connection.execute("SELECT COUNT(*) FROM messages WHERE read_at IS NULL").fetchone()[0]
        by_topic = connection.execute("SELECT topic, COUNT(*) FROM messages GROUP BY topic ORDER BY 2 DESC").fetchall()
    return {"total": total, "unread": unread, "by_topic": [[t or "other", n] for t, n in by_topic]}


def set_message_read(message_id: int, read: bool) -> bool:
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE messages SET read_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(timespec="seconds") if read else None, message_id),
        )
    return cursor.rowcount == 1


def delete_message(message_id: int) -> bool:
    with _connect() as connection:
        cursor = connection.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    return cursor.rowcount == 1
