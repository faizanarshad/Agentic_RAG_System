"""SQLite store for users, sessions, login throttling, activity events, page views and model usage."""

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


class PlatformStore:
    """Thread-safe store; every call opens its own connection."""

    def __init__(self, db_path: Optional[str] = None):
        os.makedirs(settings.PLATFORM_DATA_DIR, exist_ok=True)
        self.db_path = db_path or os.path.join(settings.PLATFORM_DATA_DIR, "platform.db")
        self._lock = threading.Lock()
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    status TEXT NOT NULL DEFAULT 'active',
                    must_change_password INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    ip TEXT,
                    user_agent TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    ip TEXT,
                    success INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_login_attempts ON login_attempts(created_at);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    workspace TEXT,
                    detail TEXT,
                    ip TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    referrer TEXT,
                    device TEXT,
                    visitor TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_page_views_created ON page_views(created_at);
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    user_id TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage(created_at);
                CREATE TABLE IF NOT EXISTS mfa_challenges (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            # Migration: two-factor authentication columns
            columns = {row[1] for row in c.execute("PRAGMA table_info(users)")}
            for name, ddl in (
                ("totp_secret", "TEXT"),
                ("totp_pending_secret", "TEXT"),
                ("totp_enabled", "INTEGER NOT NULL DEFAULT 0"),
                ("totp_last_step", "INTEGER"),
                ("recovery_codes", "TEXT"),
            ):
                if name not in columns:
                    c.execute(f"ALTER TABLE users ADD COLUMN {name} {ddl}")

    # ------------------------------------------------------------------ users

    def count_users(self, role: Optional[str] = None, status: Optional[str] = None) -> int:
        query, params = "SELECT COUNT(*) FROM users WHERE 1=1", []
        if role:
            query += " AND role = ?"
            params.append(role)
        if status:
            query += " AND status = ?"
            params.append(status)
        with self._connect() as c:
            return c.execute(query, params).fetchone()[0]

    def create_user(self, email: str, name: str, password_hash: str, role: str, must_change_password: bool) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO users (id, email, name, password_hash, role, status, must_change_password, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'active', ?, ?)",
                (user_id, email.strip().lower(), name.strip(), password_hash, role, int(must_change_password), iso(utcnow())),
            )
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as c:
            row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as c:
            row = c.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return dict(row) if row else None

    def list_users(self) -> List[Dict[str, Any]]:
        with self._connect() as c:
            rows = c.execute(
                "SELECT u.id, u.email, u.name, u.role, u.status, u.must_change_password, u.created_at, u.last_login_at, "
                "u.totp_enabled, "
                "(SELECT COUNT(*) FROM events e WHERE e.user_id = u.id AND e.created_at >= ?) AS events_30d "
                "FROM users u ORDER BY u.created_at",
                (iso(utcnow() - timedelta(days=30)),),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_user(self, user_id: str, **fields: Any) -> None:
        if not fields:
            return
        assignments = ", ".join(f"{k} = ?" for k in fields)
        with self._lock, self._connect() as c:
            c.execute(f"UPDATE users SET {assignments} WHERE id = ?", (*fields.values(), user_id))

    def delete_user(self, user_id: str) -> None:
        with self._lock, self._connect() as c:
            c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # ------------------------------------------------------------------ sessions

    def create_session(self, token_hash: str, user_id: str, ip: str, user_agent: str) -> None:
        now = utcnow()
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO sessions (token_hash, user_id, created_at, expires_at, last_seen_at, ip, user_agent) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (token_hash, user_id, iso(now), iso(now + timedelta(hours=settings.SESSION_TTL_HOURS)), iso(now),
                 ip, user_agent[:300]),
            )
            c.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (iso(now), user_id))

    def get_session_user(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Return the active user for a valid, unexpired session, refreshing last_seen."""
        now = utcnow()
        with self._connect() as c:
            row = c.execute(
                "SELECT u.*, s.expires_at, s.last_seen_at FROM sessions s JOIN users u ON u.id = s.user_id "
                "WHERE s.token_hash = ?",
                (token_hash,),
            ).fetchone()
        if row is None or row["expires_at"] < iso(now) or row["status"] != "active":
            return None
        # Throttle writes: refresh last_seen at most once a minute
        if row["last_seen_at"] < iso(now - timedelta(minutes=1)):
            with self._lock, self._connect() as c:
                c.execute("UPDATE sessions SET last_seen_at = ? WHERE token_hash = ?", (iso(now), token_hash))
        return dict(row)

    def delete_session(self, token_hash: str) -> None:
        with self._lock, self._connect() as c:
            c.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))

    def delete_user_sessions(self, user_id: str, except_token_hash: Optional[str] = None) -> int:
        with self._lock, self._connect() as c:
            cursor = c.execute(
                "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?", (user_id, except_token_hash or "")
            )
        return cursor.rowcount

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        with self._connect() as c:
            rows = c.execute(
                "SELECT token_hash, created_at, last_seen_at, expires_at, ip, user_agent FROM sessions "
                "WHERE user_id = ? AND expires_at > ? ORDER BY last_seen_at DESC",
                (user_id, iso(utcnow())),
            ).fetchall()
        return [dict(r) for r in rows]

    def purge_expired_sessions(self) -> None:
        with self._lock, self._connect() as c:
            c.execute("DELETE FROM sessions WHERE expires_at < ?", (iso(utcnow()),))

    # ------------------------------------------------------------------ two-factor challenges

    def create_mfa_challenge(self, token_hash: str, user_id: str, minutes: int = 5) -> None:
        with self._lock, self._connect() as c:
            c.execute("DELETE FROM mfa_challenges WHERE expires_at < ?", (iso(utcnow()),))
            c.execute("INSERT INTO mfa_challenges (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                      (token_hash, user_id, iso(utcnow() + timedelta(minutes=minutes))))

    def get_mfa_challenge(self, token_hash: str) -> Optional[Dict[str, Any]]:
        with self._connect() as c:
            row = c.execute("SELECT * FROM mfa_challenges WHERE token_hash = ?", (token_hash,)).fetchone()
        if row is None or row["expires_at"] < iso(utcnow()):
            return None
        return dict(row)

    def bump_mfa_attempts(self, token_hash: str) -> None:
        with self._lock, self._connect() as c:
            c.execute("UPDATE mfa_challenges SET attempts = attempts + 1 WHERE token_hash = ?", (token_hash,))

    def delete_mfa_challenge(self, token_hash: str) -> None:
        with self._lock, self._connect() as c:
            c.execute("DELETE FROM mfa_challenges WHERE token_hash = ?", (token_hash,))

    # ------------------------------------------------------------------ login throttling

    def record_login_attempt(self, email: str, ip: str, success: bool) -> None:
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO login_attempts (email, ip, success, created_at) VALUES (?, ?, ?, ?)",
                (email.strip().lower(), ip, int(success), iso(utcnow())),
            )

    def recent_failures(self, email: str, ip: str, minutes: int) -> Dict[str, int]:
        since = iso(utcnow() - timedelta(minutes=minutes))
        with self._connect() as c:
            by_email = c.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND email = ? AND created_at >= ?",
                (email.strip().lower(), since),
            ).fetchone()[0]
            by_ip = c.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND ip = ? AND created_at >= ?", (ip, since)
            ).fetchone()[0]
        return {"email": by_email, "ip": by_ip}

    # ------------------------------------------------------------------ activity events

    def log_event(self, action: str, user_id: Optional[str] = None, workspace: Optional[str] = None,
                  detail: Optional[Dict[str, Any]] = None, ip: Optional[str] = None) -> None:
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO events (user_id, action, workspace, detail, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, action, workspace, json.dumps(detail) if detail else None, ip, iso(utcnow())),
            )

    def list_events(self, limit: int = 100, offset: int = 0, user_id: Optional[str] = None,
                    action: Optional[str] = None, workspace: Optional[str] = None) -> Dict[str, Any]:
        conditions, params = [], []
        if user_id:
            conditions.append("e.user_id = ?")
            params.append(user_id)
        if action:
            conditions.append("e.action = ?")
            params.append(action)
        if workspace:
            conditions.append("e.workspace = ?")
            params.append(workspace)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._connect() as c:
            total = c.execute(f"SELECT COUNT(*) FROM events e {where}", params).fetchone()[0]
            rows = c.execute(
                f"SELECT e.*, u.email AS user_email, u.name AS user_name FROM events e "
                f"LEFT JOIN users u ON u.id = e.user_id {where} ORDER BY e.id DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
        events = []
        for row in rows:
            record = dict(row)
            record["detail"] = json.loads(record["detail"]) if record["detail"] else None
            events.append(record)
        return {"total": total, "events": events}

    def distinct_actions(self) -> List[str]:
        with self._connect() as c:
            return [r[0] for r in c.execute("SELECT DISTINCT action FROM events ORDER BY action").fetchall()]

    # ------------------------------------------------------------------ page views

    def record_page_view(self, path: str, referrer: Optional[str], device: str, visitor: str) -> None:
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO page_views (path, referrer, device, visitor, created_at) VALUES (?, ?, ?, ?, ?)",
                (path, referrer, device, visitor, iso(utcnow())),
            )

    # ------------------------------------------------------------------ model usage

    def record_llm_usage(self, model: str, feature: str, prompt_tokens: int, completion_tokens: int,
                         cost_usd: float, user_id: Optional[str]) -> None:
        with self._lock, self._connect() as c:
            c.execute(
                "INSERT INTO llm_usage (model, feature, prompt_tokens, completion_tokens, cost_usd, user_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (model, feature, prompt_tokens, completion_tokens, cost_usd, user_id, iso(utcnow())),
            )

    # ------------------------------------------------------------------ analytics queries

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._connect() as c:
            return [dict(r) for r in c.execute(sql, params).fetchall()]

    def scalar(self, sql: str, params: tuple = ()) -> Any:
        with self._connect() as c:
            return c.execute(sql, params).fetchone()[0]


_store: Optional[PlatformStore] = None
_store_lock = threading.Lock()


def get_platform_store() -> PlatformStore:
    """Process-wide store instance (cheap: connections are per call)."""
    global _store
    with _store_lock:
        if _store is None:
            _store = PlatformStore()
    return _store
