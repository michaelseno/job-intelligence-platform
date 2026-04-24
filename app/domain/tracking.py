from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.common import utcnow
from app.persistence.models import JobPosting, JobTrackingEvent


VALID_TRACKING_STATUSES = {"saved", "applied", "interview", "rejected", "offer"}


class TrackingService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def keep_job(self, job: JobPosting) -> JobPosting:
        job.manual_keep = True
        self.session.add(job)
        if not job.tracking_status:
            job.tracking_status = "saved"
            self.session.add(JobTrackingEvent(job_posting_id=job.id, event_type="save", tracking_status="saved", created_at=utcnow()))
        self.session.commit()
        self.session.refresh(job)
        return job

    def update_tracking_status(self, job: JobPosting, tracking_status: str, note_text: str | None = None) -> JobPosting:
        if tracking_status not in VALID_TRACKING_STATUSES:
            raise ValueError("Invalid tracking status.")
        job.tracking_status = tracking_status
        self.session.add(job)
        self.session.add(
            JobTrackingEvent(
                job_posting_id=job.id,
                event_type="status_change",
                tracking_status=tracking_status,
                note_text=note_text,
                created_at=utcnow(),
            )
        )
        self.session.commit()
        self.session.refresh(job)
        return job

    def list_events(self, job_id: int) -> list[JobTrackingEvent]:
        return list(
            self.session.scalars(
                select(JobTrackingEvent).where(JobTrackingEvent.job_posting_id == job_id).order_by(JobTrackingEvent.created_at.desc())
            )
        )
