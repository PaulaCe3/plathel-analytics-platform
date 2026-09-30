"""Filesystem-backed session store with expiration and safe paths."""

import re
import secrets
import shutil
import os
from threading import RLock
from weakref import WeakValueDictionary
from contextlib import contextmanager

_STORE_LOCK = RLock()
_SESSION_LOCKS = WeakValueDictionary()
from datetime import UTC, datetime, timedelta
from pathlib import Path

from analytics_core.errors import AppError
from analytics_core.sessions.models import DatasetSession

ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,64}$")


class DatasetSessionStore:
    def __init__(self, root: Path, ttl_minutes: int, absolute_ttl_minutes: int = 240) -> None:
        self.root = root.resolve()
        self.ttl = timedelta(minutes=ttl_minutes)
        self.absolute_ttl = timedelta(minutes=absolute_ttl_minutes)
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, dataset_id: str) -> Path:
        if not ID_PATTERN.fullmatch(dataset_id):
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        candidate = (self.root / dataset_id).resolve()
        if candidate.parent != self.root:
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        return candidate

    def lock(self, dataset_id):
        key = str(self._directory(dataset_id))
        with _STORE_LOCK:
            lock = _SESSION_LOCKS.get(key)
            if lock is None:
                lock = RLock()
                _SESSION_LOCKS[key] = lock
            return lock

    def create(self, industry_id: str | None = None) -> DatasetSession:
        now = datetime.now(UTC)
        while True:
            dataset_id = secrets.token_urlsafe(24)
            directory = self._directory(dataset_id)
            try:
                directory.mkdir(parents=False, mode=0o700)
                break
            except FileExistsError:
                continue
        session = DatasetSession(dataset_id=dataset_id, industry_id=industry_id, created_at=now, updated_at=now, expires_at=now + min(self.ttl, self.absolute_ttl))
        self.save(session)
        return session

    def path(self, dataset_id: str, filename: str) -> Path:
        if filename not in {"source.bin", "raw.parquet", "canonical.parquet", "session.json"}:
            raise ValueError("invalid session filename")
        directory = self._directory(dataset_id)
        path = (directory / filename).resolve()
        if path.parent != directory:
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        return path

    def save(self, session: DatasetSession) -> None:
        directory = self._directory(session.dataset_id)
        if not directory.is_dir():
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        session.updated_at = datetime.now(UTC)
        destination = self.path(session.dataset_id, "session.json")
        with _STORE_LOCK:
            temporary = directory / f"metadata-{secrets.token_hex(8)}.tmp"
            try:
                with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as output:
                    output.write(session.model_dump_json(indent=2))
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)

    def get(self, dataset_id: str, *, touch: bool = True) -> DatasetSession:
        directory = self._directory(dataset_id)
        metadata = self.path(dataset_id, "session.json")
        if not metadata.is_file():
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        session = DatasetSession.model_validate_json(metadata.read_text(encoding="utf-8"))
        if session.expires_at <= datetime.now(UTC) or session.created_at + self.absolute_ttl <= datetime.now(UTC):
            shutil.rmtree(directory, ignore_errors=True)
            raise AppError(code="DATASET_EXPIRED", http_status=410, message="La sesión del dataset expiró.")
        if touch:
            session.expires_at = min(datetime.now(UTC) + self.ttl, session.created_at + self.absolute_ttl)
            self.save(session)
        return session

    def delete(self, dataset_id: str) -> None:
        directory = self._directory(dataset_id)
        if not directory.is_dir():
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        shutil.rmtree(directory)

    def purge_expired(self) -> int:
        removed = 0
        for directory in self.root.iterdir():
            if directory.is_symlink() or not directory.is_dir() or not ID_PATTERN.fullmatch(directory.name):
                continue
            lock = self.lock(directory.name)
            if not lock.acquire(blocking=False):
                continue
            try:
                try:
                    metadata = self.path(directory.name, "session.json")
                    session = DatasetSession.model_validate_json(metadata.read_text(encoding="utf-8"))
                    expired = session.expires_at <= datetime.now(UTC) or session.created_at + self.absolute_ttl <= datetime.now(UTC)
                except FileNotFoundError:
                    try: expired = datetime.now(UTC).timestamp() - directory.stat().st_mtime > 60
                    except FileNotFoundError: continue
                except (OSError, ValueError, AppError):
                    expired = True
                if expired:
                    shutil.rmtree(directory, ignore_errors=True)
                    removed += 1
            finally:
                lock.release()
        return removed
