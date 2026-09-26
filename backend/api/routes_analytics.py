"""Cookie-less, first-party page-view analytics for the public website."""

import hashlib
import json
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Deque, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import Response

from core.config import settings
from services.platform_store import get_platform_store
from .deps import client_ip

router = APIRouter(prefix="/analytics", tags=["analytics"])

BOT_PATTERN = re.compile(r"bot|crawl|spider|slurp|lighthouse|preview|facebookexternalhit|monitor", re.IGNORECASE)
PATH_PATTERN = re.compile(r"^/[A-Za-z0-9\-._~/]{0,200}$")
EXCLUDED_PREFIXES = ("/workspace", "/admin", "/login", "/_next", "/api")
RATE_LIMIT, RATE_WINDOW = 120, 3600

_recent: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_secret_path = os.path.join(settings.PLATFORM_DATA_DIR, "analytics_secret")


def _secret() -> str:
    os.makedirs(settings.PLATFORM_DATA_DIR, exist_ok=True)
    if not os.path.exists(_secret_path):
        with open(_secret_path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(_secret_path) as f:
        return f.read().strip()


def _visitor_id(ip: str, user_agent: str) -> str:
    """Anonymous daily visitor ID: the salt changes every day and the IP is never stored."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    salt = hashlib.sha256(f"{_secret()}:{day}".encode()).hexdigest()
    return hashlib.sha256(f"{salt}:{ip}:{user_agent}".encode()).hexdigest()[:16]


def _device(user_agent: str) -> str:
    if re.search(r"iPad|Tablet", user_agent):
        return "tablet"
    if re.search(r"Mobi|Android", user_agent):
        return "mobile"
    return "desktop"


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    with _lock:
        q = _recent[ip]
        while q and now - q[0] > RATE_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return True
        q.append(now)
        return False


@router.post("/pageview", status_code=204)
async def pageview(request: Request) -> Response:
    """Accepts a text/plain JSON beacon: {"path": "/about", "referrer": "https://…"}. Always returns 204."""
    empty = Response(status_code=204)
    from services.content_store import get_content_store
    if not settings.ANALYTICS_ENABLED or not get_content_store().get_settings()["analytics_enabled"]:
        return empty
    user_agent = request.headers.get("user-agent", "")
    ip = client_ip(request)
    if not user_agent or BOT_PATTERN.search(user_agent) or _rate_limited(ip):
        return empty
    try:
        body = json.loads((await request.body())[:2000] or b"{}")
    except ValueError:
        return empty
    path = str(body.get("path") or "")
    if not PATH_PATTERN.match(path) or path.startswith(EXCLUDED_PREFIXES):
        return empty

    referrer_host = None
    referrer = str(body.get("referrer") or "")
    if referrer:
        host = (urlparse(referrer).hostname or "").lower()
        own_hosts = {urlparse(o).hostname for o in settings.FRONTEND_ORIGINS}
        if host and host not in own_hosts:
            referrer_host = host[:120]

    get_platform_store().record_page_view(path, referrer_host, _device(user_agent), _visitor_id(ip, user_agent))
    return empty
