from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.job_preferences import get_default_job_filter_preferences
from app.domain.source_batch_runs import SourceBatchExecutor, SourceBatchRunRegistry, SourceBatchRunService, build_session_factory_from_session
from app.persistence.models import Source


def add_source(session, name: str, *, health_state: str = "healthy", is_active: bool = True, deleted: bool = False) -> Source:
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
    session.flush()
    if deleted:
        source.deleted_at = source.created_at
        source.is_active = False
    session.add(source)
    session.commit()
    return source


def test_preview_run_all_partitions_non_deleted_sources(session):
    registry = SourceBatchRunRegistry()
    healthy = add_source(session, "Healthy")
    warning = add_source(session, "Warning", health_state="warning")
    inactive = add_source(session, "Inactive", is_active=False)
    add_source(session, "Deleted", deleted=True)

    preview = SourceBatchRunService(session, SourceAdapterRegistry(), registry).create_preview("all", source_ids=[warning.id])

    assert preview.eligible_count == 1
    assert preview.eligible_sources[0].source_id == healthy.id
    assert preview.skipped_count == 2
    assert {skipped.source_id for skipped in preview.skipped_sources} == {warning.id, inactive.id}


def test_preview_selected_dedupes_and_skips_missing_unhealthy(session):
    registry = SourceBatchRunRegistry()
    healthy = add_source(session, "Healthy")
    error = add_source(session, "Error", health_state="error")

    preview = SourceBatchRunService(session, SourceAdapterRegistry(), registry).create_preview(
        "selected", [healthy.id, error.id, healthy.id, 9999]
    )

    assert [source.source_id for source in preview.eligible_sources] == [healthy.id]
    assert [skipped.source_id for skipped in preview.skipped_sources] == [error.id, 9999]


def test_executor_retries_failures_and_continues(session, monkeypatch):
    state_registry = SourceBatchRunRegistry()
    adapter_registry = SourceAdapterRegistry()
    first = add_source(session, "First")
    second = add_source(session, "Second")
    preferences = get_default_job_filter_preferences()
    preview = SourceBatchRunService(session, adapter_registry, state_registry).create_preview("selected", [first.id, second.id])
    start, _ = SourceBatchRunService(session, adapter_registry, state_registry).start_batch(preview.preview_id, preferences)

    attempts: dict[int, int] = {}

    @dataclass
    class FakeRun:
        id: int
        status: str
        log_summary: str | None = None

    class FakeOrchestrator:
        def __init__(self, session, registry):
            self.session = session

        def run_source(self, source, preferences, trigger_type="manual"):
            assert trigger_type == "batch_manual"
            attempts[source.id] = attempts.get(source.id, 0) + 1
            if source.id == first.id and attempts[source.id] == 1:
                return FakeRun(id=attempts[source.id], status="failed", log_summary="temporary failure")
            if source.id == second.id:
                return FakeRun(id=100 + attempts[source.id], status="failed", log_summary="persistent failure")
            return FakeRun(id=attempts[source.id], status="success")

    monkeypatch.setattr("app.domain.source_batch_runs.IngestionOrchestrator", FakeOrchestrator)
    sleeps: list[float] = []

    SourceBatchExecutor(
        adapter_registry,
        state_registry,
        session_factory=build_session_factory_from_session(session),
        sleep=sleeps.append,
    ).execute(start.batch_id, preferences)

    status = SourceBatchRunService(session, adapter_registry, state_registry).get_status(start.batch_id)
    assert status.status == "completed_with_failures"
    assert status.success_count == 1
    assert status.failure_count == 1
    assert {result.source_id: result.attempts_used for result in status.source_results} == {first.id: 2, second.id: 3}
    assert attempts == {first.id: 2, second.id: 3}
    assert sleeps.count(1) == 2
    assert sleeps.count(2) == 1


def test_zero_eligible_start_completes_without_execution(session):
    state_registry = SourceBatchRunRegistry()
    adapter_registry = SourceAdapterRegistry()
    add_source(session, "Error", health_state="error")
    preferences = get_default_job_filter_preferences()
    preview = SourceBatchRunService(session, adapter_registry, state_registry).create_preview("all", None)

    start, status_code = SourceBatchRunService(session, adapter_registry, state_registry).start_batch(preview.preview_id, preferences)

    assert status_code == 200
    assert start.status == "completed"
    status = SourceBatchRunService(session, adapter_registry, state_registry).get_status(start.batch_id)
    assert status.eligible_count == 0
    assert status.skipped_count == 1
    assert list(session.scalars(select(Source)))
