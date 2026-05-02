from __future__ import annotations

import threading

import pytest

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.job_preferences import get_default_job_filter_preferences
from app.domain.source_batch_runs import (
    BatchConflictError,
    SourceBatchExecutor,
    SourceBatchRunRegistry,
    SourceBatchRunService,
    build_session_factory_from_session,
)
from app.persistence.models import Source
from app.schemas import SourceBatchSourceResult


def add_source(session, name: str, *, health_state: str = "healthy", is_active: bool = True) -> Source:
    source = Source(
        name=name,
        source_type="greenhouse",
        base_url=f"https://boards.greenhouse.io/{name.lower().replace(' ', '-')}",
        external_identifier=name.lower().replace(" ", "-"),
        dedupe_key=f"greenhouse||{name}",
        is_active=is_active,
        health_state=health_state,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def test_run_all_preview_ignores_supplied_selected_ids_and_partitions_all_sources(session):
    registry = SourceBatchRunRegistry()
    healthy = [add_source(session, f"Healthy {idx}") for idx in range(10)]
    unhealthy = [add_source(session, f"Unhealthy {idx}", health_state="error") for idx in range(3)]

    preview = SourceBatchRunService(session, SourceAdapterRegistry(), registry).create_preview(
        "all",
        source_ids=[unhealthy[0].id],
    )

    assert preview.eligible_count == 10
    assert {source.source_id for source in preview.eligible_sources} == {source.id for source in healthy}
    assert preview.skipped_count == 3
    assert {source.source_id for source in preview.skipped_sources} == {source.id for source in unhealthy}


def test_batch_executor_never_exceeds_five_concurrent_source_runs(session, monkeypatch):
    registry = SourceBatchRunRegistry()
    adapter_registry = SourceAdapterRegistry()
    sources = [add_source(session, f"Concurrent {idx}") for idx in range(12)]
    preferences = get_default_job_filter_preferences()
    preview = SourceBatchRunService(session, adapter_registry, registry).create_preview("selected", [source.id for source in sources])
    start, _ = SourceBatchRunService(session, adapter_registry, registry).start_batch(preview.preview_id, preferences)

    lock = threading.Lock()
    active = 0
    max_active = 0
    first_wave_ready = threading.Event()
    release_first_wave = threading.Event()

    def fake_run_source_with_retries(self, batch_id, source_ref, preferences):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
            if active == 5:
                first_wave_ready.set()

        if first_wave_ready.wait(timeout=2):
            release_first_wave.set()
        release_first_wave.wait(timeout=2)

        with lock:
            active -= 1
        self.registry.update_source_result(
            batch_id,
            SourceBatchSourceResult(
                source_id=source_ref.source_id,
                source_name=source_ref.source_name,
                status="success",
                attempts_used=1,
                source_run_ids=[source_ref.source_id],
                last_error=None,
            ),
        )

    monkeypatch.setattr(SourceBatchExecutor, "_run_source_with_retries", fake_run_source_with_retries)

    SourceBatchExecutor(
        adapter_registry,
        registry,
        session_factory=build_session_factory_from_session(session),
        sleep=lambda _: None,
    ).execute(start.batch_id, preferences)

    status = SourceBatchRunService(session, adapter_registry, registry).get_status(start.batch_id)
    assert max_active == 5
    assert status.status == "completed"
    assert status.success_count == 12
    assert status.failure_count == 0


def test_start_rejects_second_batch_while_first_is_starting(session):
    registry = SourceBatchRunRegistry()
    adapter_registry = SourceAdapterRegistry()
    first = add_source(session, "First")
    second = add_source(session, "Second")
    preferences = get_default_job_filter_preferences()
    service = SourceBatchRunService(session, adapter_registry, registry)
    first_preview = service.create_preview("selected", [first.id])
    second_preview = service.create_preview("selected", [second.id])

    first_start, status_code = service.start_batch(first_preview.preview_id, preferences)

    assert status_code == 202
    assert first_start.status == "starting"
    with pytest.raises(BatchConflictError):
        service.start_batch(second_preview.preview_id, preferences)
