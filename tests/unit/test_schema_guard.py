from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.persistence.schema_guard import (
    DatabaseSchemaOutOfDateError,
    get_repository_head_revision,
    should_validate_schema_on_startup,
    validate_database_schema_current,
)


def test_schema_guard_fails_with_actionable_message_for_stale_revision():
    engine = _engine()
    _set_revision(engine, "20260424_0002")

    with pytest.raises(DatabaseSchemaOutOfDateError) as exc_info:
        validate_database_schema_current("sqlite+pysqlite:///:memory:", engine=engine)

    message = str(exc_info.value)
    assert "Database schema is out of date" in message
    assert "alembic upgrade head" in message
    assert "20260424_0002" in message
    assert get_repository_head_revision() in message


def test_schema_guard_allows_current_head_revision():
    engine = _engine()
    _set_revision(engine, get_repository_head_revision())

    validate_database_schema_current("sqlite+pysqlite:///:memory:", engine=engine)


def test_schema_guard_ignores_metadata_only_test_database_without_alembic_version():
    engine = _engine()

    validate_database_schema_current("sqlite+pysqlite:///:memory:", engine=engine)


def test_startup_schema_guard_targets_migrated_non_sqlite_databases():
    assert should_validate_schema_on_startup("postgresql+psycopg://postgres:postgres@localhost/db") is True
    assert should_validate_schema_on_startup("sqlite:///./job_intelligence_platform.db") is False


def _engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _set_revision(engine, revision: str) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES (:revision)"), {"revision": revision})
