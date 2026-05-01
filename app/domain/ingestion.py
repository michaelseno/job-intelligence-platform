from __future__ import annotations

import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.classification import ClassificationService
from app.domain.common import fingerprint, normalize_url, payload_hash, utcnow
from app.domain.job_preferences import JobFilterPreferences
from app.domain.transient_ingestion import TransientIngestionJob, new_transient_job_id, transient_ingestion_registry
from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun


logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    def __init__(self, session: Session, registry: SourceAdapterRegistry) -> None:
        self.session = session
        self.registry = registry
        self.classifier = ClassificationService(session)

    def run_source(self, source: Source, preferences: JobFilterPreferences, trigger_type: str = "manual") -> SourceRun:
        run = SourceRun(source_id=source.id, trigger_type=trigger_type, status="running")
        self.session.add(run)
        self.session.flush()

        warnings: list[str] = []
        created = updated = unchanged = 0
        try:
            adapter = self.registry.get(source.source_type, source.adapter_key)
            validation_errors = adapter.validate_config(source)
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
            result = adapter.fetch_jobs(source)
            warnings.extend(result.warnings)
            transient_jobs: list[TransientIngestionJob] = []
            for candidate in result.jobs:
                match = self._resolve_persisted_tracked_match(source, candidate)
                if match is not None:
                    job, state = self._upsert_tracked_job(source, run, candidate, match)
                    if state == "created":
                        created += 1
                    elif state == "updated":
                        updated += 1
                    else:
                        unchanged += 1
                    self.classifier.classify_job(job, preferences)
                else:
                    transient_jobs.append(self._build_transient_job(source, run, candidate, preferences))

            transient_ingestion_registry.replace_source_results(source.id, transient_jobs)

            run.status = "success" if not warnings else "partial_success"
            run.jobs_fetched_count = len(result.jobs)
            run.jobs_created_count = created
            run.jobs_updated_count = updated
            run.jobs_unchanged_count = unchanged
            run.warning_count = len(warnings)
            run.empty_result_flag = len(result.jobs) == 0
            run.log_summary = "; ".join(warnings) if warnings else "ingestion completed"
            logger.info(
                "ingestion completed source_id=%s run_id=%s fetched=%s created=%s updated=%s unchanged=%s transient=%s",
                source.id,
                run.id,
                len(result.jobs),
                created,
                updated,
                unchanged,
                len(transient_jobs),
            )
            self._update_source_health(source, run)
        except Exception as exc:
            run.status = "failed"
            run.error_count = 1
            run.error_details_json = {"message": str(exc)}
            run.log_summary = str(exc)
            self._update_source_health(source, run)
        finally:
            run.finished_at = utcnow()
            self.session.add(run)
            self.session.commit()
            self.session.refresh(run)
        return run

    def _candidate_keys(self, candidate) -> tuple[str | None, str]:
        normalized_url = normalize_url(candidate.job_url)
        candidate_key = fingerprint(candidate.company_name, candidate.title, candidate.location_text, candidate.description_text)
        return normalized_url, candidate_key

    def _resolve_persisted_tracked_match(self, source: Source, candidate) -> JobPosting | None:
        normalized_url, candidate_key = self._candidate_keys(candidate)
        if candidate.external_job_id:
            link_match = self.session.scalar(
                select(JobSourceLink).where(
                    JobSourceLink.source_id == source.id,
                    JobSourceLink.external_job_id == candidate.external_job_id,
                )
            )
            if link_match:
                linked_job = self.session.get(JobPosting, link_match.job_posting_id)
                if linked_job is not None and linked_job.tracking_status is not None:
                    return linked_job
        return self.session.scalar(
            select(JobPosting).where(
                JobPosting.tracking_status.is_not(None),
                or_(JobPosting.normalized_job_url == normalized_url, JobPosting.canonical_key == candidate_key),
            )
        )

    def _build_transient_job(self, source: Source, run: SourceRun, candidate, preferences: JobFilterPreferences) -> TransientIngestionJob:
        normalized_url, candidate_key = self._candidate_keys(candidate)
        now = utcnow()
        snapshot = self.classifier.preview_job(candidate, preferences)
        return TransientIngestionJob(
            transient_job_id=new_transient_job_id(),
            source_id=source.id,
            source_run_id=run.id,
            external_job_id=candidate.external_job_id,
            canonical_key=candidate_key,
            normalized_job_url=normalized_url,
            title=candidate.title,
            company_name=candidate.company_name,
            job_url=candidate.job_url,
            location_text=candidate.location_text,
            employment_type=candidate.employment_type,
            remote_type=candidate.remote_type,
            description_text=candidate.description_text,
            description_html=candidate.description_html,
            sponsorship_text=candidate.sponsorship_text,
            posted_at=candidate.posted_at,
            raw_payload=candidate.raw_payload,
            classification=snapshot,
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
        )

    def _upsert_tracked_job(self, source: Source, run: SourceRun, candidate, job: JobPosting) -> tuple[JobPosting, str]:
        normalized_url = normalize_url(candidate.job_url)
        now = utcnow()
        existing_hash = payload_hash({"title": job.title, "description_text": job.description_text or "", "location_text": job.location_text or "", "job_url": job.job_url})
        incoming_hash = payload_hash({"title": candidate.title, "description_text": candidate.description_text, "location_text": candidate.location_text or "", "job_url": candidate.job_url})
        state = "unchanged" if existing_hash == incoming_hash else "updated"
        job.title = candidate.title
        job.company_name = candidate.company_name
        job.job_url = candidate.job_url
        job.normalized_job_url = normalized_url
        job.location_text = candidate.location_text
        job.employment_type = candidate.employment_type
        job.remote_type = candidate.remote_type
        job.description_text = candidate.description_text
        job.description_html = candidate.description_html
        job.sponsorship_text = candidate.sponsorship_text
        job.posted_at = candidate.posted_at
        job.last_seen_at = now
        job.last_ingested_at = now
        job.current_state = "active"

        link = self.session.scalar(
            select(JobSourceLink).where(
                JobSourceLink.job_posting_id == job.id,
                JobSourceLink.source_id == source.id,
                JobSourceLink.source_job_url == candidate.job_url,
            )
        )
        if link is None:
            link = JobSourceLink(
                job_posting_id=job.id,
                source_id=source.id,
                source_run_id=run.id,
                external_job_id=candidate.external_job_id,
                source_job_url=candidate.job_url,
                raw_payload_json=candidate.raw_payload,
                content_hash=payload_hash(candidate.raw_payload),
                is_primary=(job.primary_source_id == source.id),
                first_seen_at=now,
                last_seen_at=now,
            )
            self.session.add(link)
        else:
            link.source_run_id = run.id
            link.external_job_id = candidate.external_job_id
            link.raw_payload_json = candidate.raw_payload
            link.content_hash = payload_hash(candidate.raw_payload)
            link.last_seen_at = now
        self.session.flush()
        return job, state

    def _update_source_health(self, source: Source, run: SourceRun) -> None:
        source.last_run_at = utcnow()
        source.last_run_status = run.status
        source.last_jobs_fetched_count = run.jobs_fetched_count
        if run.status == "failed":
            source.health_state = "error"
            source.health_message = run.log_summary
        elif run.jobs_fetched_count == 0:
            source.consecutive_empty_runs += 1
            source.health_state = "warning"
            source.health_message = "Source returned zero jobs. Verify whether this is expected."
        else:
            source.consecutive_empty_runs = 0
            source.health_state = "healthy"
            source.health_message = "Recent ingestion completed successfully."
        self.session.add(source)
        self.session.flush()
