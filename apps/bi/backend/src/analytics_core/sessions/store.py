"""Filesystem-backed session store with expiration and safe paths."""

import json
import re
import secrets
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from analytics_core.errors import AppError
from analytics_core.sessions.models import DatasetSession

ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,64}$")


class DatasetSessionStore:
    def __init__(self, root: Path, ttl_minutes: int) -> None:
        self.root = root.resolve()
        self.ttl = timedelta(minutes=ttl_minutes)
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, dataset_id: str) -> Path:
        if not ID_PATTERN.fullmatch(dataset_id):
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        candidate = (self.root / dataset_id).resolve()
        if candidate.parent != self.root:
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        return candidate

    def create(self, industry_id: str | None = None) -> DatasetSession:
        now = datetime.now(UTC)
        while True:
            dataset_id = secrets.token_urlsafe(24)
            directory = self._directory(dataset_id)
            try:
                directory.mkdir(parents=False)
                break
            except FileExistsError:
                continue
        session = DatasetSession(dataset_id=dataset_id, industry_id=industry_id, created_at=now, updated_at=now, expires_at=now + self.ttl)
        self.save(session)
        return session

    def path(self, dataset_id: str, filename: str) -> Path:
        if filename not in {"source.bin", "raw.parquet"}:
            raise ValueError("invalid session filename")
        return self._directory(dataset_id) / filename

    def save(self, session: DatasetSession) -> None:
        directory = self._directory(session.dataset_id)
        directory.mkdir(exist_ok=True)
        session.updated_at = datetime.now(UTC)
        (directory / "session.json").write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def get(self, dataset_id: str, *, touch: bool = True) -> DatasetSession:
        directory = self._directory(dataset_id)
        metadata = directory / "session.json"
        if not metadata.is_file():
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        session = DatasetSession.model_validate_json(metadata.read_text(encoding="utf-8"))
        if session.expires_at <= datetime.now(UTC):
            shutil.rmtree(directory, ignore_errors=True)
            raise AppError(code="DATASET_EXPIRED", http_status=410, message="La sesión del dataset expiró.")
        if touch:
            session.expires_at = datetime.now(UTC) + self.ttl
            self.save(session)
        return session

    def delete(self, dataset_id: str) -> None:
        directory = self._directory(dataset_id)
        if not directory.is_dir():
            raise AppError(code="DATASET_NOT_FOUND", http_status=404, message="El dataset no existe.")
        shutil.rmtree(directory)

    def purge_expired(self) -> int:
        removed = 0
        for metadata in self.root.glob("*/session.json"):
            try:
                session = DatasetSession.model_validate_json(metadata.read_text(encoding="utf-8"))
                if session.expires_at <= datetime.now(UTC):
                    shutil.rmtree(metadata.parent, ignore_errors=True)
                    removed += 1
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return removed
