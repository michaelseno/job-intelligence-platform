from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError


SCHEMA_OUT_OF_DATE_MESSAGE = (
    "Database schema is out of date for this application version. "
    "Run `alembic upgrade head` against the same DATABASE_URL before starting the server."
)


class DatabaseSchemaOutOfDateError(RuntimeError):
    pass


def validate_database_schema_current(database_url: str, *, engine: Engine | None = None) -> None:
    """Fail fast when the connected database Alembic revision is behind code head.

    Databases without an Alembic version table are ignored to preserve existing test
    conventions that build an in-memory schema with SQLAlchemy metadata instead of
    running migrations. Migrated databases with an older revision fail with a clear
    operational recovery command.
    """

    owns_engine = engine is None
    check_engine = engine or create_engine(database_url, future=True)
    try:
        with check_engine.connect() as connection:
            inspector = inspect(connection)
            if not inspector.has_table("alembic_version"):
                return

            current_revisions = set(connection.execute(select(text("version_num")).select_from(text("alembic_version"))).scalars())
            head_revision = get_repository_head_revision()
            if head_revision not in current_revisions:
                current = ", ".join(sorted(current_revisions)) or "<none>"
                raise DatabaseSchemaOutOfDateError(
                    f"{SCHEMA_OUT_OF_DATE_MESSAGE} Current DB revision: {current}; required head revision: {head_revision}."
                )
    except DatabaseSchemaOutOfDateError:
        raise
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Database schema validation failed before startup: {exc}") from exc
    finally:
        if owns_engine:
            check_engine.dispose()


def should_validate_schema_on_startup(database_url: str) -> bool:
    # SQLite metadata-created test databases commonly do not use Alembic at app startup.
    # PostgreSQL/local deployment databases do, and are the environment affected here.
    return make_url(database_url).get_backend_name() != "sqlite"


def get_repository_head_revision() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(repo_root / "alembic"))
    return ScriptDirectory.from_config(alembic_cfg).get_current_head()
