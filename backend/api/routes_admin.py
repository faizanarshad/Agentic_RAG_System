"""Admin panel API: analytics, users, contact inbox, activity log and system status."""

import csv
import io
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.config import settings
from services.platform_store import get_platform_store, iso, utcnow
from services.security import hash_password, temporary_password
from . import routes_contact
from .deps import client_ip, require_admin
from .routes_auth import validate_new_password

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

ROLES = ("admin", "member")


# ---------------------------------------------------------------------- helpers

def _since(days: int) -> str:
    return iso(utcnow() - timedelta(days=days))


def _daily(table: str, days: int, value_sql: str = "COUNT(*)", where: str = "", params: tuple = ()) -> List[Dict[str, Any]]:
    """Per-day series for the last `days` days, with zero-filled gaps (UTC days).
    `where` is a trusted SQL fragment; user values go in `params`."""
    rows = get_platform_store().query(
        f"SELECT substr(created_at, 1, 10) AS day, {value_sql} AS value FROM {table} "
        f"WHERE created_at >= ? {where} GROUP BY day",
        (_since(days), *params),
    )
    by_day = {r["day"]: r["value"] or 0 for r in rows}
    start = date.today() - timedelta(days=days - 1)
    return [
        {"day": (start + timedelta(days=i)).isoformat(), "value": round(by_day.get((start + timedelta(days=i)).isoformat(), 0), 4)}
        for i in range(days)
    ]


def _content_stats() -> Dict[str, Any]:
    """Counts from the workspace stores (opened directly; no agent services are started)."""
    stats: Dict[str, Any] = {}
    try:
        from services.legal_store import LegalStore

        legal = LegalStore()
        stats["legal_documents"] = legal.count_documents()
        stats["legal_by_status"] = legal.status_counts()
    except Exception:
        stats["legal_documents"], stats["legal_by_status"] = 0, {}
    try:
        from services.engineering_store import EngineeringStore

        engineering = EngineeringStore()
        drawings = engineering.list_drawings()
        stats["drawings"] = len(drawings)
        verdicts: Dict[str, int] = {}
        findings = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        for d in drawings:
            if d.get("verdict"):
                verdicts[d["verdict"]] = verdicts.get(d["verdict"], 0) + 1
            for severity, count in (d.get("finding_counts") or {}).items():
                findings[severity] = findings.get(severity, 0) + count
        stats["drawing_verdicts"] = verdicts
        stats["drawing_findings"] = findings
        stats["comparisons"] = len(engineering.list_comparisons())
        stats["generated_documents"] = len(engineering.list_documents())
        stats["templates"] = len(engineering.list_templates())
    except Exception:
        stats.update({"drawings": 0, "drawing_verdicts": {}, "drawing_findings": {}, "comparisons": 0,
                      "generated_documents": 0, "templates": 0})
    return stats


def _csv_response(filename: str, header: List[str], rows: List[List[Any]]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        # Neutralise spreadsheet formula injection in user-supplied text
        writer.writerow([f"'{v}" if isinstance(v, str) and v[:1] in ("=", "+", "-", "@") else v for v in row])
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _dir_size_mb(path: str) -> float:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return round(total / (1024 * 1024), 1)


def _between(start_days_ago: int, end_days_ago: int) -> tuple:
    return (iso(utcnow() - timedelta(days=start_days_ago)), iso(utcnow() - timedelta(days=end_days_ago)))


def _period_metrics(start: str, end: str) -> Dict[str, float]:
    """Headline metrics for [start, end), used for current vs previous period comparisons."""
    store = get_platform_store()
    workspace = "workspace IN ('engineering','legal','medical')"
    return {
        "actions": store.scalar(f"SELECT COUNT(*) FROM events WHERE created_at >= ? AND created_at < ? AND {workspace}", (start, end)),
        "page_views": store.scalar("SELECT COUNT(*) FROM page_views WHERE created_at >= ? AND created_at < ?", (start, end)),
        "visitors": store.scalar("SELECT COUNT(DISTINCT visitor) FROM page_views WHERE created_at >= ? AND created_at < ?", (start, end)),
        "messages": store.scalar("SELECT COUNT(*) FROM events WHERE action = 'contact.message' AND created_at >= ? AND created_at < ?", (start, end)),
        "llm_cost_usd": round(store.scalar("SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE created_at >= ? AND created_at < ?", (start, end)), 4),
    }


def _deltas(days: int) -> Dict[str, Dict[str, Any]]:
    current = _period_metrics(*_between(days, -1))
    previous = _period_metrics(*_between(2 * days, days))
    result = {}
    for key, value in current.items():
        before = previous[key]
        change = None if not before else round(100 * (value - before) / before, 1)
        result[key] = {"current": value, "previous": before, "change_pct": change}
    visitors = current["visitors"]
    result["conversion_rate"] = {"current": round(100 * current["messages"] / visitors, 2) if visitors else None}
    return result


# ---------------------------------------------------------------------- analytics

@router.get("/realtime")
def realtime() -> Dict[str, Any]:
    """Visitors and pages in the last few minutes (for the live card)."""
    store = get_platform_store()
    five, thirty = _since_minutes(5), _since_minutes(30)
    return {
        "active_visitors": store.scalar("SELECT COUNT(DISTINCT visitor) FROM page_views WHERE created_at >= ?", (five,)),
        "views_30m": store.scalar("SELECT COUNT(*) FROM page_views WHERE created_at >= ?", (thirty,)),
        # Only unexpired sessions of existing, active users count as "signed in"
        "active_users": store.scalar(
            "SELECT COUNT(DISTINCT s.user_id) FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.last_seen_at >= ? AND s.expires_at > ? AND u.status = 'active'", (five, iso(utcnow()))),
        "pages": [[r["path"], r["n"]] for r in store.query(
            "SELECT path, COUNT(*) AS n FROM page_views WHERE created_at >= ? GROUP BY path ORDER BY n DESC LIMIT 6",
            (thirty,))],
    }


def _since_minutes(minutes: int) -> str:
    return iso(utcnow() - timedelta(minutes=minutes))


@router.get("/overview")
def overview(days: int = Query(default=30, ge=7, le=365)) -> Dict[str, Any]:
    store = get_platform_store()
    since = _since(days)
    workspace_rows = store.query(
        "SELECT workspace, COUNT(*) AS n FROM events WHERE created_at >= ? AND workspace IN "
        "('engineering', 'legal', 'medical') GROUP BY workspace ORDER BY n DESC",
        (since,),
    )
    return {
        "days": days,
        "kpis": {
            "active_users": store.count_users(status="active"),
            "admins": store.count_users(role="admin", status="active"),
            "signed_in_users": store.scalar(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE action = 'auth.login' AND created_at >= ?", (since,)),
            "actions": store.scalar(
                "SELECT COUNT(*) FROM events WHERE created_at >= ? AND workspace IN ('engineering','legal','medical')",
                (since,)),
            "page_views": store.scalar("SELECT COUNT(*) FROM page_views WHERE created_at >= ?", (since,)),
            "visitors": store.scalar("SELECT COUNT(DISTINCT visitor) FROM page_views WHERE created_at >= ?", (since,)),
            "llm_cost_usd": round(store.scalar(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE created_at >= ?", (since,)), 2),
            "failed_logins": store.scalar(
                "SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND created_at >= ?", (since,)),
        },
        "messages": routes_contact.message_stats(),
        "deltas": _deltas(days),
        "content": _content_stats(),
        "series": {
            "actions": _daily("events", days, where="AND workspace IN ('engineering','legal','medical')"),
            "page_views": _daily("page_views", days),
        },
        "by_workspace": [[r["workspace"], r["n"]] for r in workspace_rows],
        "recent_activity": store.list_events(limit=8)["events"],
    }


@router.get("/traffic")
def traffic(days: int = Query(default=30, ge=7, le=365)) -> Dict[str, Any]:
    store = get_platform_store()
    since = _since(days)
    return {
        "days": days,
        "totals": {
            "page_views": store.scalar("SELECT COUNT(*) FROM page_views WHERE created_at >= ?", (since,)),
            "visitors": store.scalar("SELECT COUNT(DISTINCT visitor) FROM page_views WHERE created_at >= ?", (since,)),
        },
        "series": {
            "page_views": _daily("page_views", days),
            "visitors": _daily("page_views", days, value_sql="COUNT(DISTINCT visitor)"),
        },
        "top_pages": [[r["path"], r["n"]] for r in store.query(
            "SELECT path, COUNT(*) AS n FROM page_views WHERE created_at >= ? GROUP BY path ORDER BY n DESC LIMIT 12",
            (since,))],
        "referrers": [[r["ref"], r["n"]] for r in store.query(
            "SELECT COALESCE(referrer, 'Direct / none') AS ref, COUNT(*) AS n FROM page_views WHERE created_at >= ? "
            "GROUP BY ref ORDER BY n DESC LIMIT 10", (since,))],
        "devices": [[r["device"], r["n"]] for r in store.query(
            "SELECT device, COUNT(*) AS n FROM page_views WHERE created_at >= ? GROUP BY device ORDER BY n DESC",
            (since,))],
        # First page each (daily) visitor saw
        "landing_pages": [[r["path"], r["n"]] for r in store.query(
            "SELECT v.path, COUNT(*) AS n FROM page_views v JOIN ("
            "  SELECT visitor, MIN(id) AS first_id FROM page_views WHERE created_at >= ? GROUP BY visitor"
            ") f ON f.first_id = v.id GROUP BY v.path ORDER BY n DESC LIMIT 10", (since,))],
        "top_posts": [[r["path"].replace("/blog/", ""), r["n"]] for r in store.query(
            "SELECT path, COUNT(*) AS n FROM page_views WHERE created_at >= ? AND path LIKE '/blog/%' "
            "GROUP BY path ORDER BY n DESC LIMIT 10", (since,))],
        "conversions": _daily("events", days, where="AND action = 'contact.message'"),
        "deltas": _deltas(days),
    }


@router.get("/traffic.csv")
def traffic_csv(days: int = Query(default=30, ge=7, le=365)) -> StreamingResponse:
    views = _daily("page_views", days)
    visitors = {p["day"]: p["value"] for p in _daily("page_views", days, value_sql="COUNT(DISTINCT visitor)")}
    conversions = {p["day"]: p["value"] for p in _daily("events", days, where="AND action = 'contact.message'")}
    return _csv_response(
        f"traffic-{days}d.csv",
        ["date", "page_views", "visitors", "contact_messages"],
        [[p["day"], p["value"], visitors.get(p["day"], 0), conversions.get(p["day"], 0)] for p in views],
    )


@router.get("/usage")
def usage(days: int = Query(default=30, ge=7, le=365)) -> Dict[str, Any]:
    store = get_platform_store()
    since = _since(days)
    return {
        "days": days,
        "totals": store.query(
            "SELECT COUNT(*) AS calls, COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens, "
            "COALESCE(SUM(completion_tokens), 0) AS completion_tokens, COALESCE(SUM(cost_usd), 0) AS cost_usd "
            "FROM llm_usage WHERE created_at >= ?", (since,))[0],
        "series": {"cost_usd": _daily("llm_usage", days, value_sql="SUM(cost_usd)")},
        "by_model": store.query(
            "SELECT model, COUNT(*) AS calls, SUM(prompt_tokens) AS prompt_tokens, SUM(completion_tokens) AS "
            "completion_tokens, ROUND(SUM(cost_usd), 4) AS cost_usd FROM llm_usage WHERE created_at >= ? "
            "GROUP BY model ORDER BY cost_usd DESC", (since,)),
        "by_feature": [[r["feature"], round(r["cost"], 4)] for r in store.query(
            "SELECT feature, SUM(cost_usd) AS cost FROM llm_usage WHERE created_at >= ? GROUP BY feature "
            "ORDER BY cost DESC", (since,))],
        "top_actions": [[r["action"], r["n"]] for r in store.query(
            "SELECT action, COUNT(*) AS n FROM events WHERE created_at >= ? AND action NOT LIKE 'auth.%' "
            "GROUP BY action ORDER BY n DESC LIMIT 12", (since,))],
        "by_user": store.query(
            "SELECT u.name, u.email, COUNT(e.id) AS actions FROM users u LEFT JOIN events e ON e.user_id = u.id "
            "AND e.created_at >= ? AND e.workspace IN ('engineering','legal','medical') GROUP BY u.id "
            "ORDER BY actions DESC", (since,)),
        "pricing_note": "Costs are estimates from token counts and list prices in services/usage_tracker.py.",
    }


@router.get("/system")
def system() -> Dict[str, Any]:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    storage = {name: _dir_size_mb(os.path.join(data_dir, name))
               for name in sorted(os.listdir(data_dir)) if os.path.isdir(os.path.join(data_dir, name))} \
        if os.path.isdir(data_dir) else {}
    vector = {}
    try:
        from pinecone import Pinecone

        stats = Pinecone(api_key=settings.PINECONE_API_KEY).Index(settings.PINECONE_INDEX_NAME).describe_index_stats()
        vector = {"total": stats.total_vector_count,
                  "namespaces": {ns or "default": v.vector_count for ns, v in stats.namespaces.items()}}
        vector_ok = True
    except Exception as e:
        vector_ok, vector = False, {"error": str(e)[:200]}
    return {
        "vector_db": {"ok": vector_ok, **vector},
        "storage_mb": storage,
        "models": {
            "chat": settings.OPENAI_MODEL,
            "embeddings": settings.OPENAI_EMBEDDING_MODEL,
            "legal": settings.LEGAL_MODEL,
            "engineering": settings.ENGINEERING_MODEL,
        },
        "security": {
            "cookie_secure": settings.COOKIE_SECURE,
            "session_ttl_hours": settings.SESSION_TTL_HOURS,
            "allowed_origins": settings.FRONTEND_ORIGINS,
            "analytics_enabled": settings.ANALYTICS_ENABLED,
        },
    }


# ---------------------------------------------------------------------- users

class CreateUserRequest(BaseModel):
    email: str
    name: str
    role: str = "member"


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


def _guard_last_admin(target: Dict[str, Any], new_role: Optional[str], new_status: Optional[str]) -> None:
    removing_admin = target["role"] == "admin" and target["status"] == "active" and (
        (new_role and new_role != "admin") or (new_status and new_status != "active"))
    if removing_admin and get_platform_store().count_users(role="admin", status="active") <= 1:
        raise HTTPException(status_code=400, detail="At least one active administrator is required.")


@router.get("/users")
def list_users() -> Dict[str, Any]:
    return {"users": get_platform_store().list_users()}


@router.post("/users")
def create_user(payload: CreateUserRequest, request: Request) -> Dict[str, Any]:
    store = get_platform_store()
    email = payload.email.strip().lower()
    if "@" not in email or len(email) > 254:
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if not 2 <= len(payload.name.strip()) <= 120:
        raise HTTPException(status_code=422, detail="Enter the user's name.")
    if payload.role not in ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of {list(ROLES)}.")
    if store.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="A user with this email already exists.")
    password = temporary_password()
    user = store.create_user(email, payload.name, hash_password(password), payload.role, must_change_password=True)
    store.log_event("admin.user_created", request.state.user["id"], "admin", {"email": email, "role": payload.role},
                    client_ip(request))
    # The temporary password is returned once and never stored in plain text
    return {"user": {k: user[k] for k in ("id", "email", "name", "role", "status")}, "temporary_password": password}


@router.patch("/users/{user_id}")
def update_user(user_id: str, payload: UpdateUserRequest, request: Request) -> Dict[str, Any]:
    store = get_platform_store()
    target = store.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if payload.role and payload.role not in ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of {list(ROLES)}.")
    if payload.status and payload.status not in ("active", "disabled"):
        raise HTTPException(status_code=422, detail="Status must be 'active' or 'disabled'.")
    _guard_last_admin(target, payload.role, payload.status)
    fields = {k: v for k, v in payload.dict().items() if v is not None}
    if "name" in fields:
        fields["name"] = fields["name"].strip()
    store.update_user(user_id, **fields)
    if payload.status == "disabled":
        store.delete_user_sessions(user_id)
    store.log_event("admin.user_updated", request.state.user["id"], "admin", {"user": target["email"], **fields},
                    client_ip(request))
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: str, request: Request) -> Dict[str, Any]:
    store = get_platform_store()
    target = store.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found.")
    password = temporary_password()
    store.update_user(user_id, password_hash=hash_password(password), must_change_password=1)
    store.delete_user_sessions(user_id)
    store.log_event("admin.password_reset", request.state.user["id"], "admin", {"user": target["email"]},
                    client_ip(request))
    return {"temporary_password": password}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, request: Request) -> Dict[str, Any]:
    store = get_platform_store()
    target = store.get_user(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if target["id"] == request.state.user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
    _guard_last_admin(target, "member", "disabled")
    store.delete_user(user_id)
    store.log_event("admin.user_deleted", request.state.user["id"], "admin", {"user": target["email"]},
                    client_ip(request))
    return {"ok": True}


# ---------------------------------------------------------------------- contact inbox

class MessageUpdate(BaseModel):
    read: bool


@router.get("/messages")
def messages(status: str = Query(default="all", pattern="^(all|unread|read)$"),
             limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    return {**routes_contact.list_messages(status, limit, offset), "stats": routes_contact.message_stats()}


@router.patch("/messages/{message_id}")
def update_message(message_id: int, payload: MessageUpdate) -> Dict[str, Any]:
    if not routes_contact.set_message_read(message_id, payload.read):
        raise HTTPException(status_code=404, detail="Message not found.")
    return {"ok": True}


@router.delete("/messages/{message_id}")
def delete_message(message_id: int, request: Request) -> Dict[str, Any]:
    if not routes_contact.delete_message(message_id):
        raise HTTPException(status_code=404, detail="Message not found.")
    get_platform_store().log_event("admin.message_deleted", request.state.user["id"], "admin", {"id": message_id},
                                   client_ip(request))
    return {"ok": True}


@router.get("/messages.csv")
def messages_csv() -> StreamingResponse:
    items = routes_contact.list_messages("all", 100000, 0)["messages"]
    return _csv_response(
        "contact-messages.csv",
        ["id", "created_at", "name", "email", "company", "topic", "message", "read_at"],
        [[m["id"], m["created_at"], m["name"], m["email"], m["company"], m["topic"], m["message"], m["read_at"]]
         for m in items],
    )


# ---------------------------------------------------------------------- activity log

@router.get("/activity")
def activity(limit: int = Query(default=50, ge=1, le=500), offset: int = Query(default=0, ge=0),
             user_id: Optional[str] = None, action: Optional[str] = None,
             workspace: Optional[str] = None) -> Dict[str, Any]:
    store = get_platform_store()
    return {**store.list_events(limit, offset, user_id, action, workspace), "actions": store.distinct_actions()}


@router.get("/activity.csv")
def activity_csv(user_id: Optional[str] = None, action: Optional[str] = None,
                 workspace: Optional[str] = None) -> StreamingResponse:
    events = get_platform_store().list_events(100000, 0, user_id, action, workspace)["events"]
    return _csv_response(
        "activity-log.csv",
        ["id", "created_at", "user", "action", "workspace", "detail", "ip"],
        [[e["id"], e["created_at"], e["user_email"] or "", e["action"], e["workspace"] or "",
          "" if e["detail"] is None else str(e["detail"]), e["ip"] or ""] for e in events],
    )
