"""SQLite persistence for engineering drawings, comparisons, templates and generated documents."""

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import settings
from .engineering_templates import BUILTIN_TEMPLATES


JSON_COLUMNS = {
    "pages", "cad", "extraction", "rule_checks", "review", "result", "sections", "missing_information", "source_ids",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EngineeringStore:
    """Thread-safe SQLite store; each call opens its own connection."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the store, create tables and seed the built-in templates."""
        os.makedirs(settings.ENGINEERING_DATA_DIR, exist_ok=True)
        self.db_path = db_path or os.path.join(settings.ENGINEERING_DATA_DIR, "engineering.db")
        self._write_lock = threading.Lock()
        self._create_tables()
        self._seed_templates()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS drawings (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    source_type TEXT,
                    page_count INTEGER,
                    pages TEXT,
                    cad TEXT,
                    standard TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    extraction TEXT,
                    rule_checks TEXT,
                    review TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS comparisons (
                    id TEXT PRIMARY KEY,
                    a_id TEXT NOT NULL,
                    b_id TEXT NOT NULL,
                    result TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    sections TEXT NOT NULL,
                    builtin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    template_id TEXT,
                    template_name TEXT,
                    title TEXT,
                    sections TEXT,
                    missing_information TEXT,
                    source_ids TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def _seed_templates(self) -> None:
        now = _now()
        with self._write_lock, self._connect() as connection:
            for template in BUILTIN_TEMPLATES:
                connection.execute(
                    "INSERT OR IGNORE INTO templates (id, name, description, category, sections, builtin, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
                    (template["id"], template["name"], template["description"], template["category"],
                     json.dumps(template["sections"]), now, now),
                )

    # ----- generic helpers -----

    def _insert(self, table: str, record: Dict[str, Any]) -> None:
        values = [json.dumps(v) if k in JSON_COLUMNS else v for k, v in record.items()]
        columns = ", ".join(record)
        placeholders = ", ".join("?" for _ in record)
        with self._write_lock, self._connect() as connection:
            connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)

    def _update(self, table: str, record_id: str, fields: Dict[str, Any]) -> None:
        if table != "comparisons":
            fields["updated_at"] = _now()
        values = [json.dumps(v) if k in JSON_COLUMNS else v for k, v in fields.items()]
        assignments = ", ".join(f"{k} = ?" for k in fields)
        with self._write_lock, self._connect() as connection:
            connection.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", (*values, record_id))

    def _get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return self._decode(row) if row else None

    def _delete(self, table: str, record_id: str) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))

    @staticmethod
    def _decode(row: sqlite3.Row) -> Dict[str, Any]:
        record = dict(row)
        for key in JSON_COLUMNS & set(record):
            if record[key]:
                record[key] = json.loads(record[key])
        if "builtin" in record:
            record["builtin"] = bool(record["builtin"])
        return record

    # ----- drawings -----

    def create_drawing(self, drawing_id: str, filename: str, file_path: str, standard: str) -> None:
        now = _now()
        self._insert("drawings", {
            "id": drawing_id, "filename": filename, "file_path": file_path, "standard": standard,
            "status": "processing", "created_at": now, "updated_at": now,
        })

    def update_drawing(self, drawing_id: str, **fields: Any) -> None:
        self._update("drawings", drawing_id, fields)

    def get_drawing(self, drawing_id: str) -> Optional[Dict[str, Any]]:
        return self._get("drawings", drawing_id)

    def list_drawings(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, filename, source_type, page_count, standard, status, error, review, extraction, created_at "
                "FROM drawings ORDER BY created_at DESC"
            ).fetchall()
        drawings = []
        for row in rows:
            record = self._decode(row)
            review = record.pop("review") or {}
            title_block = (record.pop("extraction") or {}).get("title_block") or {}
            findings = review.get("findings") or []
            record.update({
                "verdict": review.get("verdict"),
                "drawing_number": title_block.get("drawing_number"),
                "title": title_block.get("title"),
                "revision": title_block.get("revision"),
                "finding_counts": {
                    severity: sum(1 for f in findings if f.get("severity") == severity)
                    for severity in ("critical", "major", "minor", "info")
                },
            })
            drawings.append(record)
        return drawings

    def delete_drawing(self, drawing_id: str) -> None:
        self._delete("drawings", drawing_id)

    # ----- comparisons -----

    def create_comparison(self, a_id: str, b_id: str, result: Dict[str, Any]) -> str:
        comparison_id = str(uuid.uuid4())
        self._insert("comparisons", {
            "id": comparison_id, "a_id": a_id, "b_id": b_id, "result": result, "created_at": _now(),
        })
        return comparison_id

    def get_comparison(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        return self._get("comparisons", comparison_id)

    def list_comparisons(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM comparisons ORDER BY created_at DESC").fetchall()
        return [self._decode(row) for row in rows]

    # ----- templates -----

    def list_templates(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM templates ORDER BY builtin DESC, name").fetchall()
        return [self._decode(row) for row in rows]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        return self._get("templates", template_id)

    def create_template(self, template: Dict[str, Any]) -> str:
        template_id = str(uuid.uuid4())
        now = _now()
        self._insert("templates", {
            "id": template_id,
            "name": template["name"],
            "description": template.get("description", ""),
            "category": template.get("category", "custom"),
            "sections": template["sections"],
            "builtin": 0,
            "created_at": now,
            "updated_at": now,
        })
        return template_id

    def update_template(self, template_id: str, template: Dict[str, Any]) -> None:
        self._update("templates", template_id, {
            "name": template["name"],
            "description": template.get("description", ""),
            "category": template.get("category", "custom"),
            "sections": template["sections"],
        })

    def delete_template(self, template_id: str) -> None:
        self._delete("templates", template_id)

    # ----- generated documents -----

    def create_document(self, document: Dict[str, Any]) -> str:
        document_id = str(uuid.uuid4())
        now = _now()
        self._insert("documents", {"id": document_id, **document, "created_at": now, "updated_at": now})
        return document_id

    def update_document(self, document_id: str, **fields: Any) -> None:
        self._update("documents", document_id, fields)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        return self._get("documents", document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, template_id, template_name, title, created_at, updated_at FROM documents "
                "ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_document(self, document_id: str) -> None:
        self._delete("documents", document_id)
