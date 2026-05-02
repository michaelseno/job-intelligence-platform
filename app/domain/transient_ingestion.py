from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from uuid import uuid4

from app.domain.classification import ClassificationSnapshot


@dataclass(frozen=True)
class TransientIngestionJob:
    transient_job_id: str
    source_id: int
    source_run_id: int
    external_job_id: str | None
    canonical_key: str
    normalized_job_url: str | None
    title: str
    company_name: str | None
    job_url: str
    location_text: str | None
    employment_type: str | None
    remote_type: str | None
    description_text: str
    description_html: str | None
    sponsorship_text: str | None
    posted_at: datetime | None
    raw_payload: dict
    classification: ClassificationSnapshot
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime


class TransientIngestionRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._by_id: dict[str, TransientIngestionJob] = {}
        self._ids_by_source: dict[int, set[str]] = {}
        self._ids_by_run: dict[int, set[str]] = {}

    def replace_source_results(self, source_id: int, jobs: list[TransientIngestionJob]) -> None:
        with self._lock:
            for transient_job_id in self._ids_by_source.get(source_id, set()).copy():
                self._remove_locked(transient_job_id)
            deduped: dict[tuple[str, str], TransientIngestionJob] = {}
            for job in jobs:
                if job.external_job_id:
                    key = ("external", f"{job.source_id}:{job.external_job_id}")
                elif job.normalized_job_url:
                    key = ("url", job.normalized_job_url)
                else:
                    key = ("canonical", job.canonical_key)
                deduped[key] = job
            for job in deduped.values():
                self._by_id[job.transient_job_id] = job
                self._ids_by_source.setdefault(job.source_id, set()).add(job.transient_job_id)
                self._ids_by_run.setdefault(job.source_run_id, set()).add(job.transient_job_id)

    def list(self, source_id: int | None = None) -> list[TransientIngestionJob]:
        with self._lock:
            if source_id is None:
                return list(self._by_id.values())
            ids = self._ids_by_source.get(source_id, set())
            return [self._by_id[job_id] for job_id in ids if job_id in self._by_id]

    def get(self, transient_job_id: str) -> TransientIngestionJob | None:
        with self._lock:
            return self._by_id.get(transient_job_id)

    def consume(self, transient_job_id: str) -> TransientIngestionJob | None:
        with self._lock:
            job = self._by_id.get(transient_job_id)
            if job is None:
                return None
            self._remove_locked(transient_job_id)
            return job

    def clear(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_source.clear()
            self._ids_by_run.clear()

    def _remove_locked(self, transient_job_id: str) -> None:
        job = self._by_id.pop(transient_job_id, None)
        if job is None:
            return
        source_ids = self._ids_by_source.get(job.source_id)
        if source_ids is not None:
            source_ids.discard(transient_job_id)
            if not source_ids:
                self._ids_by_source.pop(job.source_id, None)
        run_ids = self._ids_by_run.get(job.source_run_id)
        if run_ids is not None:
            run_ids.discard(transient_job_id)
            if not run_ids:
                self._ids_by_run.pop(job.source_run_id, None)


transient_ingestion_registry = TransientIngestionRegistry()


def new_transient_job_id() -> str:
    return str(uuid4())
