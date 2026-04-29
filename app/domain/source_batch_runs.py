from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Literal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.ingestion import IngestionOrchestrator
from app.domain.job_preferences import JobFilterPreferences
from app.persistence.db import SessionLocal
from app.persistence.models import Source
from app.schemas import (
    SourceBatchRunPreviewResponse,
    SourceBatchRunStartResponse,
    SourceBatchRunStatusResponse,
    SourceBatchSkippedSource,
    SourceBatchSourceRef,
    SourceBatchSourceResult,
)

logger = logging.getLogger(__name__)

BatchMode = Literal["all", "selected"]
ACTIVE_STATUSES = {"starting", "running"}
SUCCESS_STATUSES = {"success", "partial_success"}
MAX_CONCURRENCY = 5
MAX_ATTEMPTS = 3
PREVIEW_TTL = timedelta(minutes=10)
BATCH_TTL = timedelta(minutes=30)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BatchPreview:
    preview_id: str
    mode: BatchMode
    eligible_sources: list[SourceBatchSourceRef]
    skipped_sources: list[SourceBatchSkippedSource]
    created_at: datetime
    expires_at: datetime


@dataclass
class BatchState:
    batch_id: str
    mode: BatchMode
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    eligible_sources: list[SourceBatchSourceRef]
    skipped_sources: list[SourceBatchSkippedSource]
    source_results: list[SourceBatchSourceResult]
    error_message: str | None = None
    expires_at: datetime | None = None


class SourceBatchRunRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._previews: dict[str, BatchPreview] = {}
        self._batches: dict[str, BatchState] = {}

    def cleanup(self) -> None:
        now = utcnow()
        with self._lock:
            for preview_id, preview in list(self._previews.items()):
                if preview.expires_at <= now:
                    self._previews.pop(preview_id, None)
            for batch_id, batch in list(self._batches.items()):
                if batch.expires_at and batch.expires_at <= now:
                    self._batches.pop(batch_id, None)

    def add_preview(self, preview: BatchPreview) -> None:
        with self._lock:
            self._previews[preview.preview_id] = preview

    def consume_preview(self, preview_id: str) -> tuple[BatchPreview | None, bool]:
        with self._lock:
            preview = self._previews.pop(preview_id, None)
            if preview is None:
                return None, False
            if preview.expires_at <= utcnow():
                return None, True
            return preview, False

    def has_active_batch(self) -> bool:
        with self._lock:
            return any(batch.status in ACTIVE_STATUSES for batch in self._batches.values())

    def add_batch(self, batch: BatchState) -> None:
        with self._lock:
            self._batches[batch.batch_id] = batch

    def get_batch(self, batch_id: str) -> BatchState | None:
        with self._lock:
            batch = self._batches.get(batch_id)
            return self._copy_batch(batch) if batch else None

    def mark_batch_running(self, batch_id: str) -> None:
        with self._lock:
            batch = self._batches[batch_id]
            batch.status = "running"
            batch.started_at = utcnow()

    def mark_batch_failed(self, batch_id: str, message: str) -> None:
        with self._lock:
            batch = self._batches[batch_id]
            batch.status = "failed"
            batch.error_message = message
            batch.finished_at = utcnow()
            batch.expires_at = batch.finished_at + BATCH_TTL

    def mark_batch_completed(self, batch_id: str) -> None:
        with self._lock:
            batch = self._batches[batch_id]
            failures = sum(1 for result in batch.source_results if result.status == "failed")
            batch.status = "completed_with_failures" if failures else "completed"
            batch.finished_at = utcnow()
            batch.expires_at = batch.finished_at + BATCH_TTL

    def update_source_result(self, batch_id: str, result: SourceBatchSourceResult) -> None:
        with self._lock:
            batch = self._batches[batch_id]
            for idx, existing in enumerate(batch.source_results):
                if existing.source_id == result.source_id:
                    batch.source_results[idx] = result
                    return
            batch.source_results.append(result)

    def _copy_batch(self, batch: BatchState) -> BatchState:
        return BatchState(
            batch_id=batch.batch_id,
            mode=batch.mode,
            status=batch.status,
            created_at=batch.created_at,
            started_at=batch.started_at,
            finished_at=batch.finished_at,
            eligible_sources=list(batch.eligible_sources),
            skipped_sources=list(batch.skipped_sources),
            source_results=list(batch.source_results),
            error_message=batch.error_message,
            expires_at=batch.expires_at,
        )


registry = SourceBatchRunRegistry()


class SourceBatchRunService:
    def __init__(self, session: Session, adapter_registry: SourceAdapterRegistry, state_registry: SourceBatchRunRegistry = registry) -> None:
        self.session = session
        self.adapter_registry = adapter_registry
        self.registry = state_registry

    def create_preview(self, mode: BatchMode, source_ids: list[int] | None) -> SourceBatchRunPreviewResponse:
        self.registry.cleanup()
        eligible, skipped = self._partition_sources(mode, source_ids)
        now = utcnow()
        preview = BatchPreview(
            preview_id=str(uuid4()),
            mode=mode,
            eligible_sources=eligible,
            skipped_sources=skipped,
            created_at=now,
            expires_at=now + PREVIEW_TTL,
        )
        self.registry.add_preview(preview)
        logger.info(
            "source batch preview created",
            extra={"preview_id": preview.preview_id, "mode": mode, "eligible_count": len(eligible), "skipped_count": len(skipped)},
        )
        return self._preview_response(preview)

    def start_batch(self, preview_id: str, preferences: JobFilterPreferences) -> tuple[SourceBatchRunStartResponse, int]:
        self.registry.cleanup()
        if self.registry.has_active_batch():
            raise BatchConflictError("Another source batch run is already starting or running.")
        preview, expired = self.registry.consume_preview(preview_id)
        if expired:
            raise BatchPreviewExpiredError("Batch preview expired.")
        if preview is None:
            raise BatchPreviewNotFoundError("Batch preview not found.")

        now = utcnow()
        batch_id = str(uuid4())
        results = [
            SourceBatchSourceResult(source_id=source.source_id, source_name=source.source_name, status="pending", attempts_used=0, source_run_ids=[])
            for source in preview.eligible_sources
        ]
        status = "starting" if preview.eligible_sources else "completed"
        batch = BatchState(
            batch_id=batch_id,
            mode=preview.mode,
            status=status,
            created_at=now,
            started_at=None,
            finished_at=now if not preview.eligible_sources else None,
            eligible_sources=preview.eligible_sources,
            skipped_sources=preview.skipped_sources,
            source_results=results,
            expires_at=(now + BATCH_TTL) if not preview.eligible_sources else None,
        )
        if not preview.eligible_sources:
            batch.expires_at = now + BATCH_TTL
        self.registry.add_batch(batch)
        logger.info(
            "source batch started",
            extra={"batch_id": batch_id, "mode": preview.mode, "eligible_count": len(preview.eligible_sources), "skipped_count": len(preview.skipped_sources)},
        )
        return self._start_response(batch), 202 if preview.eligible_sources else 200

    def get_status(self, batch_id: str) -> SourceBatchRunStatusResponse | None:
        self.registry.cleanup()
        batch = self.registry.get_batch(batch_id)
        return self._status_response(batch) if batch else None

    def _partition_sources(self, mode: BatchMode, source_ids: list[int] | None) -> tuple[list[SourceBatchSourceRef], list[SourceBatchSkippedSource]]:
        if mode == "all":
            sources = list(self.session.scalars(select(Source).where(Source.deleted_at.is_(None)).order_by(Source.name.asc(), Source.id.asc())))
            return self._partition_existing_sources(sources)

        deduped_ids = self._dedupe_ids(source_ids or [])
        sources_by_id = {source.id: source for source in self.session.scalars(select(Source).where(Source.id.in_(deduped_ids)))} if deduped_ids else {}
        eligible: list[SourceBatchSourceRef] = []
        skipped: list[SourceBatchSkippedSource] = []
        for source_id in deduped_ids:
            source = sources_by_id.get(source_id)
            if source is None:
                skipped.append(SourceBatchSkippedSource(source_id=source_id, source_name=f"Source {source_id}", health_state=None, reason="Source not found."))
                continue
            self._append_partition(source, eligible, skipped)
        return eligible, skipped

    def _partition_existing_sources(self, sources: list[Source]) -> tuple[list[SourceBatchSourceRef], list[SourceBatchSkippedSource]]:
        eligible: list[SourceBatchSourceRef] = []
        skipped: list[SourceBatchSkippedSource] = []
        for source in sources:
            self._append_partition(source, eligible, skipped)
        return eligible, skipped

    def _append_partition(self, source: Source, eligible: list[SourceBatchSourceRef], skipped: list[SourceBatchSkippedSource]) -> None:
        if source.deleted_at is not None:
            skipped.append(SourceBatchSkippedSource(source_id=source.id, source_name=source.name, health_state=source.health_state, reason="Source is deleted."))
        elif not source.is_active:
            skipped.append(SourceBatchSkippedSource(source_id=source.id, source_name=source.name, health_state=source.health_state, reason="Source is inactive."))
        elif source.health_state != "healthy":
            skipped.append(SourceBatchSkippedSource(source_id=source.id, source_name=source.name, health_state=source.health_state, reason=f"Source health is {source.health_state}."))
        else:
            eligible.append(SourceBatchSourceRef(source_id=source.id, source_name=source.name, health_state=source.health_state))

    def _dedupe_ids(self, source_ids: list[int]) -> list[int]:
        seen: set[int] = set()
        deduped: list[int] = []
        for source_id in source_ids:
            if source_id not in seen:
                seen.add(source_id)
                deduped.append(source_id)
        return deduped

    def _preview_response(self, preview: BatchPreview) -> SourceBatchRunPreviewResponse:
        return SourceBatchRunPreviewResponse(
            preview_id=preview.preview_id,
            mode=preview.mode,
            eligible_count=len(preview.eligible_sources),
            skipped_count=len(preview.skipped_sources),
            eligible_sources=preview.eligible_sources,
            skipped_sources=preview.skipped_sources,
            expires_at=preview.expires_at,
        )

    def _start_response(self, batch: BatchState) -> SourceBatchRunStartResponse:
        return SourceBatchRunStartResponse(
            batch_id=batch.batch_id,
            status=batch.status,
            mode=batch.mode,
            eligible_count=len(batch.eligible_sources),
            skipped_count=len(batch.skipped_sources),
            poll_url=f"/sources/batch-runs/{batch.batch_id}",
        )

    def _status_response(self, batch: BatchState) -> SourceBatchRunStatusResponse:
        success_count = sum(1 for result in batch.source_results if result.status == "success")
        failure_count = sum(1 for result in batch.source_results if result.status == "failed")
        pending_count = sum(1 for result in batch.source_results if result.status == "pending")
        running_count = sum(1 for result in batch.source_results if result.status == "running")
        completed_count = success_count + failure_count
        return SourceBatchRunStatusResponse(
            batch_id=batch.batch_id,
            mode=batch.mode,
            status=batch.status,
            eligible_count=len(batch.eligible_sources),
            skipped_count=len(batch.skipped_sources),
            success_count=success_count,
            failure_count=failure_count,
            pending_count=pending_count,
            running_count=running_count,
            completed_count=completed_count,
            started_at=batch.started_at,
            finished_at=batch.finished_at,
            source_results=batch.source_results,
            skipped_sources=batch.skipped_sources,
            error_message=batch.error_message,
        )


class SourceBatchExecutor:
    def __init__(
        self,
        adapter_registry: SourceAdapterRegistry,
        state_registry: SourceBatchRunRegistry = registry,
        session_factory: Callable[[], Session] = SessionLocal,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.adapter_registry = adapter_registry
        self.registry = state_registry
        self.session_factory = session_factory
        self.sleep = sleep

    def execute(self, batch_id: str, preferences: JobFilterPreferences) -> None:
        batch = self.registry.get_batch(batch_id)
        if batch is None:
            logger.warning("source batch execution skipped; batch missing", extra={"batch_id": batch_id})
            return
        try:
            self.registry.mark_batch_running(batch_id)
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
                futures = [pool.submit(self._run_source_with_retries, batch_id, source, preferences) for source in batch.eligible_sources]
                for future in as_completed(futures):
                    future.result()
            self.registry.mark_batch_completed(batch_id)
            completed = self.registry.get_batch(batch_id)
            logger.info("source batch completed", extra={"batch_id": batch_id, "status": completed.status if completed else None})
        except Exception as exc:
            logger.exception("source batch failed", extra={"batch_id": batch_id})
            self.registry.mark_batch_failed(batch_id, str(exc))

    def _run_source_with_retries(self, batch_id: str, source_ref: SourceBatchSourceRef, preferences: JobFilterPreferences) -> None:
        run_ids: list[int] = []
        last_error: str | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.registry.update_source_result(
                batch_id,
                SourceBatchSourceResult(
                    source_id=source_ref.source_id,
                    source_name=source_ref.source_name,
                    status="running",
                    attempts_used=attempt,
                    source_run_ids=run_ids,
                    last_error=last_error,
                ),
            )
            logger.info("source batch attempt started", extra={"batch_id": batch_id, "source_id": source_ref.source_id, "attempt": attempt})
            try:
                with self.session_factory() as session:
                    source = session.get(Source, source_ref.source_id)
                    if source is None or source.deleted_at is not None or not source.is_active:
                        last_error = "Source became unavailable before execution."
                        self.registry.update_source_result(
                            batch_id,
                            SourceBatchSourceResult(
                                source_id=source_ref.source_id,
                                source_name=source_ref.source_name,
                                status="failed",
                                attempts_used=attempt - 1,
                                source_run_ids=run_ids,
                                last_error=last_error,
                            ),
                        )
                        logger.info("source batch source unavailable", extra={"batch_id": batch_id, "source_id": source_ref.source_id})
                        return
                    run = IngestionOrchestrator(session, self.adapter_registry).run_source(source, preferences, trigger_type="batch_manual")
                    run_ids.append(run.id)
                    last_error = run.log_summary if run.status == "failed" else None
                    logger.info(
                        "source batch attempt finished",
                        extra={"batch_id": batch_id, "source_id": source_ref.source_id, "attempt": attempt, "source_run_id": run.id, "status": run.status},
                    )
                    if run.status in SUCCESS_STATUSES:
                        self.registry.update_source_result(
                            batch_id,
                            SourceBatchSourceResult(
                                source_id=source_ref.source_id,
                                source_name=source_ref.source_name,
                                status="success",
                                attempts_used=attempt,
                                source_run_ids=run_ids,
                                last_error=None,
                            ),
                        )
                        return
            except Exception as exc:
                last_error = str(exc)
                logger.exception("source batch attempt raised", extra={"batch_id": batch_id, "source_id": source_ref.source_id, "attempt": attempt})

            if attempt < MAX_ATTEMPTS:
                self.sleep(attempt)

        self.registry.update_source_result(
            batch_id,
            SourceBatchSourceResult(
                source_id=source_ref.source_id,
                source_name=source_ref.source_name,
                status="failed",
                attempts_used=MAX_ATTEMPTS,
                source_run_ids=run_ids,
                last_error=last_error,
            ),
        )
        logger.info("source batch source final result", extra={"batch_id": batch_id, "source_id": source_ref.source_id, "status": "failed"})


class BatchPreviewNotFoundError(ValueError):
    pass


class BatchPreviewExpiredError(ValueError):
    pass


class BatchConflictError(ValueError):
    pass


def build_session_factory_from_session(session: Session) -> sessionmaker[Session]:
    return sessionmaker(bind=session.get_bind(), autoflush=False, autocommit=False, future=True)
