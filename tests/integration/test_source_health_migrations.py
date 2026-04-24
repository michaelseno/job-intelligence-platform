from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.operations import OperationsService
from app.persistence.models import Source, utcnow


REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
ACTIVE_SOURCE_UNIQUE_INDEX = "ix_sources_dedupe_key_active_unique"
LEGACY_SOURCE_UNIQUE_CONSTRAINT = "uq_sources_dedupe_key"


def _run_alembic_upgrade(database_url: str, revision: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", revision],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_alembic_upgrade_adds_deleted_at_and_enforces_active_source_uniqueness(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'source-health-migration.sqlite'}"

    _run_alembic_upgrade(database_url, "20260423_0001")
    initial_engine = create_engine(database_url, future=True)
    initial_columns = {column["name"] for column in inspect(initial_engine).get_columns("sources")}
    assert "deleted_at" not in initial_columns
    initial_engine.dispose()

    _run_alembic_upgrade(database_url, "head")
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("sources")}
    assert "deleted_at" in columns

    fk_tables = {
        "source_runs": "source_id",
        "job_postings": "primary_source_id",
        "job_source_links": "source_id",
    }
    for table_name, constrained_column in fk_tables.items():
        assert any(
            foreign_key["referred_table"] == "sources"
            and constrained_column in foreign_key["constrained_columns"]
            for foreign_key in inspector.get_foreign_keys(table_name)
        )

    assert LEGACY_SOURCE_UNIQUE_CONSTRAINT not in {
        constraint["name"] for constraint in inspector.get_unique_constraints("sources")
    }
    assert any(index["name"] == ACTIVE_SOURCE_UNIQUE_INDEX for index in inspector.get_indexes("sources"))

    with Session(engine) as session:
        service = OperationsService(session)
        source = Source(
            name="Legacy Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/legacy",
            external_identifier="legacy",
            dedupe_key="greenhouse||https://boards.greenhouse.io/legacy|legacy",
            is_active=True,
        )
        session.add(source)
        session.commit()

        assert [item.name for item in service.list_source_health()] == ["Legacy Source"]

        duplicate_active = Source(
            name="Duplicate Active Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/legacy-copy",
            external_identifier="legacy-copy",
            dedupe_key=source.dedupe_key,
            is_active=True,
        )
        session.add(duplicate_active)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        source.deleted_at = utcnow()
        source.is_active = False
        session.add(source)
        session.commit()

        replacement = Source(
            name="Replacement Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/replacement",
            external_identifier="replacement",
            dedupe_key=source.dedupe_key,
            is_active=True,
        )
        session.add(replacement)
        session.commit()

        assert [item.name for item in service.list_source_health()] == ["Replacement Source"]

    engine.dispose()
