from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.classification import ClassificationService
from app.domain.common import payload_hash, utcnow
from app.domain.transient_ingestion import TransientIngestionJob, transient_ingestion_registry
from app.persistence.models import JobPosting, JobSourceLink, JobTrackingEvent


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

    def track_transient_job(self, transient_job_id: str, tracking_status: str, note_text: str | None = None) -> tuple[JobPosting, bool]:
        if not tracking_status or tracking_status not in VALID_TRACKING_STATUSES:
            raise ValueError("Invalid tracking status.")
        transient = transient_ingestion_registry.get(transient_job_id)
        if transient is None:
            raise LookupError("Transient job not found.")
        try:
            job = self._find_existing_match(transient)
            if job is not None and job.tracking_status is None:
                raise RuntimeError("Transient job matches an untracked persisted row. Refresh ingestion after cleanup.")
            created = job is None
            now = utcnow()
            if job is None:
                job = JobPosting(
                    canonical_key=transient.canonical_key,
                    primary_source_id=transient.source_id,
                    title=transient.title,
                    company_name=transient.company_name,
                    job_url=transient.job_url,
                    normalized_job_url=transient.normalized_job_url,
                    location_text=transient.location_text,
                    employment_type=transient.employment_type,
                    remote_type=transient.remote_type,
                    description_text=transient.description_text,
                    description_html=transient.description_html,
                    sponsorship_text=transient.sponsorship_text,
                    posted_at=transient.posted_at,
                    first_seen_at=transient.first_seen_at,
                    last_seen_at=now,
                    last_ingested_at=now,
                    tracking_status=tracking_status,
                )
                self.session.add(job)
                self.session.flush()
            else:
                self._update_job_from_transient(job, transient, tracking_status, now)
            self._upsert_source_link(job, transient, now)
            ClassificationService(self.session).persist_snapshot(job, transient.classification)
            self.session.add(
                JobTrackingEvent(
                    job_posting_id=job.id,
                    event_type="save" if tracking_status == "saved" else "status_change",
                    tracking_status=tracking_status,
                    note_text=note_text,
                    created_at=now,
                )
            )
            self.session.commit()
            transient_ingestion_registry.consume(transient_job_id)
            self.session.refresh(job)
            return job, created
        except Exception:
            self.session.rollback()
            raise

    def _find_existing_match(self, transient: TransientIngestionJob) -> JobPosting | None:
        if transient.external_job_id:
            link_match = self.session.scalar(
                select(JobSourceLink).where(
                    JobSourceLink.source_id == transient.source_id,
                    JobSourceLink.external_job_id == transient.external_job_id,
                )
            )
            if link_match:
                return self.session.get(JobPosting, link_match.job_posting_id)
        return self.session.scalar(
            select(JobPosting).where(
                or_(
                    JobPosting.normalized_job_url == transient.normalized_job_url,
                    JobPosting.canonical_key == transient.canonical_key,
                )
            )
        )

    def _update_job_from_transient(self, job: JobPosting, transient: TransientIngestionJob, tracking_status: str, now) -> None:
        job.title = transient.title
        job.company_name = transient.company_name
        job.job_url = transient.job_url
        job.normalized_job_url = transient.normalized_job_url
        job.location_text = transient.location_text
        job.employment_type = transient.employment_type
        job.remote_type = transient.remote_type
        job.description_text = transient.description_text
        job.description_html = transient.description_html
        job.sponsorship_text = transient.sponsorship_text
        job.posted_at = transient.posted_at
        job.last_seen_at = now
        job.last_ingested_at = now
        job.current_state = "active"
        job.tracking_status = tracking_status
        self.session.add(job)

    def _upsert_source_link(self, job: JobPosting, transient: TransientIngestionJob, now) -> JobSourceLink:
        link = self.session.scalar(
            select(JobSourceLink).where(
                JobSourceLink.job_posting_id == job.id,
                JobSourceLink.source_id == transient.source_id,
                JobSourceLink.source_job_url == transient.job_url,
            )
        )
        if link is None:
            link = JobSourceLink(
                job_posting_id=job.id,
                source_id=transient.source_id,
                source_run_id=transient.source_run_id,
                external_job_id=transient.external_job_id,
                source_job_url=transient.job_url,
                raw_payload_json=transient.raw_payload,
                content_hash=payload_hash(transient.raw_payload),
                is_primary=(job.primary_source_id == transient.source_id),
                first_seen_at=transient.first_seen_at,
                last_seen_at=now,
            )
            self.session.add(link)
        else:
            link.source_run_id = transient.source_run_id
            link.external_job_id = transient.external_job_id
            link.raw_payload_json = transient.raw_payload
            link.content_hash = payload_hash(transient.raw_payload)
            link.last_seen_at = now
        self.session.flush()
        return link

    def list_events(self, job_id: int) -> list[JobTrackingEvent]:
        return list(
            self.session.scalars(
                select(JobTrackingEvent).where(JobTrackingEvent.job_posting_id == job_id).order_by(JobTrackingEvent.created_at.desc())
            )
        )
