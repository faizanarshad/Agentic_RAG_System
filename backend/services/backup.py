"""Backups of every database and uploaded file, with rotation and verified restore.

Databases are copied with SQLite's online backup API, so a backup is consistent even while the API is running.
The encryption key file (encryption.key) is deliberately left out: store it (or DATA_ENCRYPTION_KEY) separately,
so a stolen backup cannot decrypt 2FA secrets. Archives are written with owner-only permissions.
"""

import os
import shutil
import sqlite3
import tarfile
import tempfile
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.config import settings
from utils.logger import logger

ARCHIVE_PREFIX = "aidocumentagent-backup-"
EXCLUDED_NAMES = {"encryption.key"}


def _sources() -> Dict[str, str]:
    """Archive folder name -> data directory."""
    from api import routes_contact  # its path is patched in tests
    return {
        "platform": settings.PLATFORM_DATA_DIR,
        "legal": settings.LEGAL_DATA_DIR,
        "engineering": settings.ENGINEERING_DATA_DIR,
        "contact": routes_contact.DATA_DIR,
    }


def _copy_tree(source: str, target: str) -> None:
    """Copy a data directory: databases through the backup API, other files as-is (minus secrets and WAL files)."""
    for root, _dirs, files in os.walk(source):
        relative = os.path.relpath(root, source)
        os.makedirs(os.path.join(target, relative), exist_ok=True)
        for name in files:
            if name in EXCLUDED_NAMES or name.endswith(("-wal", "-shm", "-journal")):
                continue
            src, dst = os.path.join(root, name), os.path.join(target, relative, name)
            if name.endswith(".db"):
                with sqlite3.connect(src, timeout=30) as source_db, sqlite3.connect(dst) as target_db:
                    source_db.backup(target_db)
                target_db.close()
            else:
                shutil.copy2(src, dst)


def create_backup(backup_dir: Optional[str] = None, keep: Optional[int] = None) -> str:
    """Write a .tar.gz of all data, delete the oldest archives beyond `keep`, and return the archive path."""
    backup_dir = backup_dir or settings.BACKUP_DIR
    keep = settings.BACKUP_KEEP if keep is None else keep
    os.makedirs(backup_dir, mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = os.path.join(backup_dir, f"{ARCHIVE_PREFIX}{stamp}.tar.gz")
    with tempfile.TemporaryDirectory() as staging:
        for name, source in _sources().items():
            if os.path.isdir(source):
                _copy_tree(source, os.path.join(staging, name))
        fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle, tarfile.open(fileobj=handle, mode="w:gz") as tar:
            for name in sorted(os.listdir(staging)):
                tar.add(os.path.join(staging, name), arcname=name)
    for old in list_backups(backup_dir)[keep:]:
        os.remove(old)
    logger.info(f"Backup written: {archive}")
    return archive


def list_backups(backup_dir: Optional[str] = None) -> List[str]:
    """Backup archives, newest first."""
    backup_dir = backup_dir or settings.BACKUP_DIR
    if not os.path.isdir(backup_dir):
        return []
    names = [n for n in os.listdir(backup_dir) if n.startswith(ARCHIVE_PREFIX) and n.endswith(".tar.gz")]
    return [os.path.join(backup_dir, n) for n in sorted(names, reverse=True)]


def verify_backup(archive: str) -> List[str]:
    """Extract to a temporary folder and run SQLite's integrity check on every database. Returns the problems."""
    problems = []
    with tempfile.TemporaryDirectory() as staging:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(staging, filter="data")  # the 'data' filter blocks absolute paths, links and '..'
        databases = [os.path.join(r, n) for r, _d, fs in os.walk(staging) for n in fs if n.endswith(".db")]
        if not databases:
            problems.append("archive contains no databases")
        for path in databases:
            with sqlite3.connect(path) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            connection.close()
            if result != "ok":
                problems.append(f"{os.path.relpath(path, staging)}: {result}")
    return problems


def restore_backup(archive: str) -> Dict[str, str]:
    """Replace the current data with a verified backup. Run only while the API is stopped.

    Current data folders are kept beside the originals as <folder>.pre-restore-<time> for rollback.
    """
    problems = verify_backup(archive)
    if problems:
        raise ValueError("Backup failed verification: " + "; ".join(problems))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    moved = {}
    with tempfile.TemporaryDirectory() as staging:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(staging, filter="data")
        for name, target in _sources().items():
            restored = os.path.join(staging, name)
            if not os.path.isdir(restored):
                continue
            if os.path.isdir(target):
                previous = f"{target.rstrip(os.sep)}.pre-restore-{stamp}"
                shutil.move(target, previous)
                moved[name] = previous
                key = os.path.join(previous, "encryption.key")
                if os.path.exists(key):  # the key is never in backups; carry the current one over
                    os.makedirs(restored, exist_ok=True)
                    shutil.copy2(key, os.path.join(restored, "encryption.key"))
            shutil.move(restored, target)
    logger.info(f"Restored backup {archive}")
    return moved


_scheduler_started = False


def start_scheduler() -> None:
    """Take a backup every BACKUP_INTERVAL_HOURS in a daemon thread (0 disables)."""
    global _scheduler_started
    hours = settings.BACKUP_INTERVAL_HOURS
    if hours <= 0 or _scheduler_started:
        return
    _scheduler_started = True
    stop = threading.Event()

    def run() -> None:
        latest = list_backups()
        # Catch up at startup if the newest backup is older than the interval
        if latest:
            age_hours = (datetime.now().timestamp() - os.path.getmtime(latest[0])) / 3600
            wait = max(0.0, hours - age_hours) * 3600
        else:
            wait = 60
        while not stop.wait(wait):
            try:
                create_backup()
            except Exception as e:
                logger.error(f"Scheduled backup failed: {e}")
            wait = hours * 3600

    threading.Thread(target=run, name="backup-scheduler", daemon=True).start()
