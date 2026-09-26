"""Contact form endpoint for the public website."""

import os
import re
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Deque, Dict

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

_recent: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


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


def _rate_limited(client_ip: str) -> bool:
    now = time.monotonic()
    with _lock:
        timestamps = _recent[client_ip]
        while timestamps and now - timestamps[0] > RATE_WINDOW_SECONDS:
            timestamps.popleft()
        if len(timestamps) >= RATE_LIMIT:
            return True
        timestamps.append(now)
        return False


@router.post("")
def submit_contact(payload: ContactMessage, request: Request) -> Dict[str, bool]:
    """Validate and store a contact message."""
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

    client_ip = request.client.host if request.client else "unknown"
    if _rate_limited(client_ip):
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
    return {"ok": True}
