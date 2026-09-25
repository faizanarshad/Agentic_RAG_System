"""SQLite persistence for legal documents, their analyses and ingestion batches."""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import settings


JSON_COLUMNS = ("ocr_pages", "classification", "extraction", "risks", "summary")

# Columns returned by list queries (excludes the full document text and heavy JSON)
SUMMARY_COLUMNS = (
    "id, filename, batch_id, status, error, doc_type, subtype, title, overall_risk, "
    "risk_score, governing_law, page_count, created_at, updated_at"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LegalStore:
    """Thread-safe SQLite store; each call opens its own connection."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the store and create tables if needed."""
        os.makedirs(settings.LEGAL_DATA_DIR, exist_ok=True)
        self.db_path = db_path or os.path.join(settings.LEGAL_DATA_DIR, "legal.db")
        self._write_lock = threading.Lock()
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT,
                    batch_id TEXT,
                    status TEXT NOT NULL,
                    error TEXT,
                    doc_type TEXT,
                    subtype TEXT,
                    title TEXT,
                    overall_risk TEXT,
                    risk_score INTEGER,
                    governing_law TEXT,
                    page_count INTEGER,
                    ocr_pages TEXT,
                    text TEXT,
                    classification TEXT,
                    extraction TEXT,
                    risks TEXT,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
                CREATE INDEX IF NOT EXISTS idx_documents_batch ON documents(batch_id);
                CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);

                CREATE TABLE IF NOT EXISTS batches (
                    id TEXT PRIMARY KEY,
                    total INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # ----- documents -----

    def create_document(self, doc_id: str, filename: str, file_path: str, batch_id: Optional[str]) -> None:
        """Insert a newly uploaded document in the 'queued' state."""
        now = _now()
        with self._write_lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO documents (id, filename, file_path, batch_id, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'queued', ?, ?)",
                (doc_id, filename, file_path, batch_id, now, now),
            )

    def update_document(self, doc_id: str, **fields: Any) -> None:
        """Update columns of a document; dict/list values are stored as JSON."""
        if not fields:
            return
        fields["updated_at"] = _now()
        values = [json.dumps(value) if key in JSON_COLUMNS else value for key, value in fields.items()]
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self._write_lock, self._connect() as connection:
            connection.execute(f"UPDATE documents SET {assignments} WHERE id = ?", (*values, doc_id))

    def claim_document(self, doc_id: str) -> bool:
        """Atomically move a queued document to 'processing'; False if another worker already has it."""
        with self._write_lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE documents SET status = 'processing', error = NULL, updated_at = ? "
                "WHERE id = ? AND status = 'queued'",
                (_now(), doc_id),
            )
        return cursor.rowcount == 1

    def requeue_unfinished(self) -> List[str]:
        """Reset documents left queued or mid-processing (e.g. by a restart) to 'queued' and return their IDs."""
        with self._write_lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM documents WHERE status IN ('queued', 'processing') ORDER BY created_at"
            ).fetchall()
            connection.execute("UPDATE documents SET status = 'queued' WHERE status = 'processing'")
        return [row["id"] for row in rows]

    def get_document(self, doc_id: str, include_text: bool = False) -> Optional[Dict[str, Any]]:
        """Return a full document record, or None if it does not exist."""
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if row is None:
            return None
        record = self._decode(row)
        if not include_text:
            record.pop("text", None)
        record.pop("file_path", None)
        return record

    def get_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Return full records (without text) for several documents, in the given order."""
        if not doc_ids:
            return []
        placeholders = ", ".join("?" for _ in doc_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM documents WHERE id IN ({placeholders})", doc_ids
            ).fetchall()
        by_id = {}
        for row in rows:
            record = self._decode(row)
            record.pop("text", None)
            record.pop("file_path", None)
            by_id[record["id"]] = record
        return [by_id[doc_id] for doc_id in doc_ids if doc_id in by_id]

    def get_file_path(self, doc_id: str) -> Optional[str]:
        with self._connect() as connection:
            row = connection.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return row["file_path"] if row else None

    def list_documents(
        self,
        doc_type: Optional[str] = None,
        overall_risk: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List documents (without text) with optional filters and pagination."""
        conditions, params = [], []
        if doc_type:
            conditions.append("doc_type = ?")
            params.append(doc_type)
        if overall_risk:
            conditions.append("overall_risk = ?")
            params.append(overall_risk)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if search:
            conditions.append("(filename LIKE ? OR title LIKE ? OR subtype LIKE ?)")
            params.extend([f"%{search}%"] * 3)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as connection:
            total = connection.execute(f"SELECT COUNT(*) FROM documents {where}", params).fetchone()[0]
            rows = connection.execute(
                f"SELECT {SUMMARY_COLUMNS} FROM documents {where} ORDER BY created_at DESC, filename "
                f"LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
        return {"total": total, "documents": [dict(row) for row in rows]}

    def all_analyzed(self) -> List[Dict[str, Any]]:
        """Return every completed document's structured analysis (no text) for corpus statistics."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, filename, title, doc_type, subtype, overall_risk, risk_score, governing_law, "
                "page_count, ocr_pages, extraction, risks FROM documents WHERE status = 'completed'"
            ).fetchall()
        return [self._decode(row) for row in rows]

    def status_counts(self) -> Dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute("SELECT status, COUNT(*) AS n FROM documents GROUP BY status").fetchall()
        return {row["status"]: row["n"] for row in rows}

    def count_documents(self) -> int:
        with self._connect() as connection:
            return connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    def delete_document(self, doc_id: str) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    # ----- batches -----

    def create_batch(self, batch_id: str, total: int) -> None:
        with self._write_lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO batches (id, total, created_at) VALUES (?, ?, ?)", (batch_id, total, _now())
            )

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Return a batch with per-status document counts."""
        with self._connect() as connection:
            batch = connection.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
            if batch is None:
                return None
            rows = connection.execute(
                "SELECT status, COUNT(*) AS n FROM documents WHERE batch_id = ? GROUP BY status", (batch_id,)
            ).fetchall()
        counts = {row["status"]: row["n"] for row in rows}
        done = counts.get("completed", 0) + counts.get("failed", 0)
        return {
            "id": batch["id"],
            "total": batch["total"],
            "created_at": batch["created_at"],
            "counts": counts,
            "done": done,
            "finished": done >= batch["total"],
        }

    def latest_batch_id(self) -> Optional[str]:
        with self._connect() as connection:
            row = connection.execute("SELECT id FROM batches ORDER BY created_at DESC LIMIT 1").fetchone()
        return row["id"] if row else None

    @staticmethod
    def _decode(row: sqlite3.Row) -> Dict[str, Any]:
        record = dict(row)
        for key in JSON_COLUMNS:
            if key in record and record[key]:
                record[key] = json.loads(record[key])
        return record
