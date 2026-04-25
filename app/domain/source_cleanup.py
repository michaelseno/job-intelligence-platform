from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import delete, distinct, or_, select
from sqlalchemy.orm import Session

from app.persistence.models import (
    DigestItem,
    JobDecision,
    JobDecisionRule,
    JobPosting,
    JobSourceLink,
    JobTrackingEvent,
    Reminder,
    Source,
    SourceRun,
    utcnow,
)

logger = logging.getLogger(__name__)

SOURCE_DELETE_CLEANUP_TRIGGER = "source_delete_cleanup"


@dataclass(frozen=True)
class SourceDeleteCleanupResult:
    source_id: int
    status: str
    associated_count: int = 0
    retained_count: int = 0
    deleted_count: int = 0
    run_id: int | None = None


class SourceDeleteCleanupService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def cleanup_source(self, source_id: int) -> SourceDeleteCleanupResult:
        source = self.session.get(Source, source_id)
        if source is None:
            logger.info("source delete cleanup skipped; source not found", extra={"source_id": source_id})
            return SourceDeleteCleanupResult(source_id=source_id, status="skipped_source_not_found")
        if source.deleted_at is None:
            logger.info("source delete cleanup skipped; source is not deleted", extra={"source_id": source_id})
            return SourceDeleteCleanupResult(source_id=source_id, status="skipped_source_not_deleted")

        run = SourceRun(source_id=source_id, trigger_type=SOURCE_DELETE_CLEANUP_TRIGGER, status="running")
        self.session.add(run)
        self.session.flush()
        run_id = run.id
        self.session.commit()

        try:
            associated_ids = self._associated_job_ids(source_id)
            retained_ids = self._retained_job_ids(associated_ids)
            delete_ids = [job_id for job_id in associated_ids if job_id not in retained_ids]

            deleted_count = self._delete_jobs(delete_ids)

            run.status = "success"
            run.finished_at = utcnow()
            run.jobs_fetched_count = len(associated_ids)
            run.empty_result_flag = len(associated_ids) == 0
            run.log_summary = (
                f"Source delete cleanup evaluated {len(associated_ids)} job(s), "
                f"retained {len(retained_ids)}, deleted {deleted_count}."
            )
            run.error_details_json = {
                "source_id": source_id,
                "associated_count": len(associated_ids),
                "retained_count": len(retained_ids),
                "deleted_count": deleted_count,
            }
            self.session.add(run)
            self.session.commit()
            logger.info(
                "source delete cleanup completed",
                extra={
                    "source_id": source_id,
                    "cleanup_run_id": run_id,
                    "associated_count": len(associated_ids),
                    "retained_count": len(retained_ids),
                    "deleted_count": deleted_count,
                    "status": "success",
                },
            )
            return SourceDeleteCleanupResult(
                source_id=source_id,
                status="success",
                associated_count=len(associated_ids),
                retained_count=len(retained_ids),
                deleted_count=deleted_count,
                run_id=run_id,
            )
        except Exception as exc:
            self.session.rollback()
            failed_run = self.session.get(SourceRun, run_id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.finished_at = utcnow()
                failed_run.error_count = 1
                failed_run.log_summary = "Source delete cleanup failed."
                failed_run.error_details_json = {"source_id": source_id, "error": str(exc), "error_type": type(exc).__name__}
                self.session.add(failed_run)
                self.session.commit()
            logger.exception("source delete cleanup failed", extra={"source_id": source_id, "cleanup_run_id": run_id})
            raise

    def _associated_job_ids(self, source_id: int) -> list[int]:
        query = (
            select(distinct(JobPosting.id))
            .outerjoin(JobSourceLink, JobSourceLink.job_posting_id == JobPosting.id)
            .where(or_(JobPosting.primary_source_id == source_id, JobSourceLink.source_id == source_id))
        )
        return list(self.session.scalars(query))

    def _retained_job_ids(self, job_ids: list[int]) -> set[int]:
        if not job_ids:
            return set()
        query = select(JobPosting.id).where(
            JobPosting.id.in_(job_ids),
            JobPosting.latest_bucket == "matched",
            JobPosting.current_state == "active",
        )
        return set(self.session.scalars(query))

    def _delete_jobs(self, job_ids: list[int]) -> int:
        if not job_ids:
            return 0

        decision_ids = list(self.session.scalars(select(JobDecision.id).where(JobDecision.job_posting_id.in_(job_ids))))
        if decision_ids:
            self.session.execute(delete(JobDecisionRule).where(JobDecisionRule.job_decision_id.in_(decision_ids)))
        self.session.execute(delete(JobDecision).where(JobDecision.job_posting_id.in_(job_ids)))
        self.session.execute(delete(JobTrackingEvent).where(JobTrackingEvent.job_posting_id.in_(job_ids)))
        self.session.execute(delete(Reminder).where(Reminder.job_posting_id.in_(job_ids)))
        self.session.execute(delete(DigestItem).where(DigestItem.job_posting_id.in_(job_ids)))
        self.session.execute(delete(JobSourceLink).where(JobSourceLink.job_posting_id.in_(job_ids)))
        result = self.session.execute(
            delete(JobPosting).where(
                JobPosting.id.in_(job_ids),
                or_(
                    JobPosting.latest_bucket.is_(None),
                    JobPosting.latest_bucket != "matched",
                    JobPosting.current_state.is_(None),
                    JobPosting.current_state != "active",
                ),
            )
        )
        return int(result.rowcount or 0)


def run_source_delete_cleanup(source_id: int) -> None:
    from app.persistence.db import SessionLocal

    with SessionLocal() as session:
        SourceDeleteCleanupService(session).cleanup_source(source_id)
