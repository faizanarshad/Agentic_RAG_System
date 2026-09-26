"""Origin guard (CSRF defence) and automatic activity logging for workspace actions."""

import re

from fastapi import Request
from fastapi.responses import JSONResponse

from core.config import settings
from services.platform_store import get_platform_store
from utils.logger import logger

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# (method, path pattern, action, workspace): successful requests are recorded in the activity log
ACTIVITY_RULES = [
    ("POST", r"^/chat/$", "medical.ask", "medical"),
    ("POST", r"^/files/add_file$", "medical.upload", "medical"),
    ("PUT", r"^/files/update_file/", "medical.replace", "medical"),
    ("DELETE", r"^/files/delete_file/", "medical.delete", "medical"),
    ("POST", r"^/legal/batches$", "legal.batch_upload", "legal"),
    ("POST", r"^/legal/ask$", "legal.ask", "legal"),
    ("POST", r"^/legal/search$", "legal.search", "legal"),
    ("POST", r"^/legal/synthesize$", "legal.synthesize", "legal"),
    ("POST", r"^/legal/documents/[^/]+/retry$", "legal.reanalyze", "legal"),
    ("DELETE", r"^/legal/documents/", "legal.delete", "legal"),
    ("POST", r"^/engineering/drawings$", "engineering.review", "engineering"),
    ("POST", r"^/engineering/drawings/[^/]+/review$", "engineering.re_review", "engineering"),
    ("POST", r"^/engineering/drawings/[^/]+/ask$", "engineering.ask", "engineering"),
    ("DELETE", r"^/engineering/drawings/", "engineering.delete_drawing", "engineering"),
    ("POST", r"^/engineering/compare$", "engineering.compare", "engineering"),
    ("POST", r"^/engineering/templates$", "engineering.template_create", "engineering"),
    ("PUT", r"^/engineering/templates/", "engineering.template_update", "engineering"),
    ("POST", r"^/engineering/templates/import$", "engineering.template_import", "engineering"),
    ("POST", r"^/engineering/templates/[^/]+/review$", "engineering.template_review", "engineering"),
    ("POST", r"^/engineering/documents/generate$", "engineering.generate_document", "engineering"),
    ("GET", r"^/engineering/documents/[^/]+/export$", "engineering.export", "engineering"),
]
_COMPILED = [(m, re.compile(p), a, w) for m, p, a, w in ACTIVITY_RULES]


async def security_headers(request: Request, call_next):
    """Defence-in-depth headers on every API response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
    if request.url.path.startswith(("/auth", "/admin")):
        # Account and admin data must never be stored by browsers or proxies
        response.headers["Cache-Control"] = "no-store"
    return response


async def origin_guard(request: Request, call_next):
    """Browsers always send Origin on cross-origin unsafe requests; reject unknown origins."""
    origin = request.headers.get("origin")
    if request.method in UNSAFE_METHODS and origin and origin.rstrip("/") not in settings.FRONTEND_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "Origin not allowed."})
    return await call_next(request)


async def activity_logger(request: Request, call_next):
    response = await call_next(request)
    if response.status_code < 400:
        user = getattr(request.state, "user", None)
        if user:
            for method, pattern, action, workspace in _COMPILED:
                if request.method == method and pattern.match(request.url.path):
                    try:
                        get_platform_store().log_event(
                            action, user["id"], workspace, {"path": request.url.path},
                            request.client.host if request.client else None,
                        )
                    except Exception as e:
                        logger.warning(f"Could not log activity: {str(e)}")
                    break
    return response
