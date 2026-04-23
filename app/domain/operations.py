from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import Source, SourceRun


class OperationsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_source_health(self) -> list[Source]:
        return list(self.session.scalars(select(Source).order_by(Source.name.asc())))

    def list_runs(self) -> list[SourceRun]:
        return list(self.session.scalars(select(SourceRun).order_by(SourceRun.started_at.desc())))

    def get_run(self, run_id: int) -> SourceRun | None:
        return self.session.get(SourceRun, run_id)
