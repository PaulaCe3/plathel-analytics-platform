from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from analytics_core.errors import AppError
from analytics_core.sessions.store import DatasetSessionStore, ID_PATTERN


def test_dataset_id_is_opaque_and_path_safe(tmp_path: Path) -> None:
    store = DatasetSessionStore(tmp_path, 60)
    first = store.create()
    second = store.create()
    assert first.dataset_id != second.dataset_id
    assert ID_PATTERN.fullmatch(first.dataset_id)
    with pytest.raises(AppError):
        store.get("../escape")


def test_expired_session_is_deleted(tmp_path: Path) -> None:
    store = DatasetSessionStore(tmp_path, 60)
    session = store.create()
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    store.save(session)
    with pytest.raises(AppError) as error:
        store.get(session.dataset_id)
    assert error.value.code == "DATASET_EXPIRED"
    assert not (tmp_path / session.dataset_id).exists()
