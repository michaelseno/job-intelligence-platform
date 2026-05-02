# Bug Report

## 1. Summary

Full regression validation for `feature/transient_untracked_ingestion_jobs` is blocked by three failure groups: stale tests that still expect ingestion to persist untracked jobs, SQLite in-memory session/thread isolation in source-delete/background-cleanup and batch-executor tests, and UI shell tests that instantiate the app without the repository test DB fixture.

## 2. Investigation Context

- Source of report: QA full-suite regression.
- Branch: `feature/transient_untracked_ingestion_jobs`.
- Related feature/workflow: transient untracked ingestion jobs.
- QA report: `docs/qa/transient_untracked_ingestion_jobs_test_report.md`.
- Failing QA command: `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest`.
- Reproduction performed locally on 2026-05-01:
  - Full suite reproduced 17 failures, 113 passed, 4 warnings.
  - Isolated batch executor test reproduced the 18th QA-reported failure.

## 3. Observed Symptoms

### Group A: tests still expect newly ingested untracked jobs in persisted `/jobs` JSON

Affected tests observed in full-suite output:

- `tests/integration/test_html_views.py::test_dashboard_and_jobs_html_render`
- `tests/integration/test_html_views.py::test_html_forms_redirect_for_source_and_tracking`
- `tests/integration/test_html_views.py::test_jobs_html_treats_empty_source_filter_as_unset`
- `tests/ui/test_source_edit_delete_ui_qa.py::test_source_delete_confirmation_explains_async_cleanup_and_retention`
- `tests/ui/test_source_edit_delete_ui_qa.py::test_deleted_source_non_retained_job_uses_normal_not_found`

Exact failure shape:

- `IndexError: list index out of range` at `client.get("/jobs").json()[0]`.
- Examples:
  - `tests/integration/test_html_views.py:48`
  - `tests/integration/test_html_views.py:76`
  - `tests/ui/test_source_edit_delete_ui_qa.py:74`
  - `tests/ui/test_source_edit_delete_ui_qa.py:195`

Expected by old tests: ingestion creates a persisted job row immediately, so `/jobs` JSON contains at least one item.

Expected by current feature spec: new untracked ingestion results are transient runtime data only and are not returned by persisted JSON `/jobs` until the user tracks them.

### Group B: source delete tests fail when background cleanup opens a different in-memory SQLite session

Affected tests observed in full-suite output:

- `tests/api/test_source_edit_delete_qa.py::test_deleted_and_nonexistent_source_endpoints_return_not_found`
- `tests/integration/test_api_flow.py::test_source_patch_delete_and_delete_impact_flow`
- `tests/integration/test_api_flow.py::test_deleted_sources_are_removed_from_html_filters_and_inactive_sources_cannot_run`
- `tests/integration/test_source_edit_delete_html.py::test_source_delete_html_flow_hides_deleted_source_from_management_surfaces`

Exact failure excerpt:

```text
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: sources
[SQL: SELECT sources.id AS sources_id, ... FROM sources WHERE sources.id = ?]
[parameters: (1,)]
```

Stack path:

```text
app/web/routes.py:845 enqueue_source_delete_cleanup(background_tasks, source.id)
app/web/routes.py:440 background_tasks.add_task(run_source_delete_cleanup, source_id)
app/domain/source_cleanup.py:156 run_source_delete_cleanup
app/domain/source_cleanup.py:157 from app.persistence.db import SessionLocal
app/domain/source_cleanup.py:159 with SessionLocal() as session
app/domain/source_cleanup.py:160 SourceDeleteCleanupService(session).cleanup_source(source_id)
app/domain/source_cleanup.py:42 source = self.session.get(Source, source_id)
```

### Group C: global UI shell tests use app `SessionLocal` without test schema/fixtures

Affected tests observed in full-suite output:

- `tests/ui/test_saas_dashboard_ui_revamp.py::test_dashboard_renders_html_shell`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_jobs_index_renders_management_table_ui`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_job_detail_renders_html_detail_view`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_sources_index_renders_management_table_ui`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_detail_renders_html_detail_view`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_create_validation_uses_html_error_state`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_source_health_renders_in_shared_shell`
- `tests/ui/test_saas_dashboard_ui_revamp.py::test_tracking_page_renders_in_shared_shell`

Exact failure shape:

- HTML shell requests return `500 Internal Server Error` instead of expected `200` or `400`.
- `tests/ui/test_saas_dashboard_ui_revamp.py:7` defines `client = TestClient(app, raise_server_exceptions=False)` at module scope.
- These tests do not use the repository `client` fixture in `tests/conftest.py`, so they do not get `Base.metadata.create_all(engine)` or `app.dependency_overrides[get_session_dependency]`.

### Group D: isolated batch executor test marks successful fake runs as failed under threaded in-memory SQLite

Affected test:

- `tests/unit/test_source_batch_run_qa_validation.py::test_batch_executor_never_exceeds_five_concurrent_source_runs`

Isolated reproduction:

```text
assert status.status == "completed"
E AssertionError: assert 'completed_with_failures' == 'completed'
```

Captured root exception before the failed status:

```text
ERROR app.domain.source_batch_runs:source_batch_runs.py:405 source batch attempt raised
sqlalchemy.exc.InterfaceError: (sqlite3.InterfaceError) bad parameter or other API misuse
[SQL: SELECT sources.id AS sources_id, ... FROM sources WHERE sources.id = ?]
[parameters: (4,)]
```

Failure point:

```text
app/domain/source_batch_runs.py:366 with self.session_factory() as session
app/domain/source_batch_runs.py:367 source = session.get(Source, source_ref.source_id)
```

## 4. Evidence Collected

Files inspected:

- `docs/qa/transient_untracked_ingestion_jobs_test_report.md`
- `docs/product/transient_untracked_ingestion_jobs_product_spec.md`
- `tests/conftest.py`
- `tests/integration/test_html_views.py`
- `tests/ui/test_source_edit_delete_ui_qa.py`
- `tests/ui/test_saas_dashboard_ui_revamp.py`
- `tests/api/test_source_edit_delete_qa.py`
- `tests/integration/test_api_flow.py`
- `tests/integration/test_source_edit_delete_html.py`
- `tests/unit/test_source_batch_run_qa_validation.py`
- `app/domain/ingestion.py`
- `app/domain/tracking.py`
- `app/domain/source_cleanup.py`
- `app/domain/source_batch_runs.py`
- `app/persistence/db.py`
- `app/web/routes.py`

Key evidence:

- Product spec requires no DB persistence for newly ingested untracked jobs: `docs/product/transient_untracked_ingestion_jobs_product_spec.md:69-83`, especially FR 3-4 and 10-12.
- Ingestion implementation matches that rule: `app/domain/ingestion.py:41-54` resolves only persisted tracked matches; otherwise appends candidates to `transient_jobs`; `app/domain/ingestion.py:54` replaces runtime registry results.
- JSON `/jobs` remains persisted-only: `app/web/routes.py:985-990` returns `jobs` before HTML transient-card merge.
- HTML `/jobs` merges transient cards only for HTML responses: `app/web/routes.py:992-1000`.
- Test DB fixture creates a per-test StaticPool in-memory DB and overrides only request dependency injection: `tests/conftest.py:24-49`.
- Source cleanup bypasses the request dependency override and imports production `SessionLocal`: `app/domain/source_cleanup.py:156-160`.
- App `SessionLocal` is bound once to `app.persistence.db.engine`: `app/persistence/db.py:17-19`; for `sqlite+pysqlite:///:memory:` it does not create schema by itself.
- UI shell tests bypass the fixture: `tests/ui/test_saas_dashboard_ui_revamp.py:7`.
- Batch executor test shares the test session bind across multiple worker sessions/threads: `tests/unit/test_source_batch_run_qa_validation.py:95-99`; helper `build_session_factory_from_session` binds new sessions to `session.get_bind()`: `app/domain/source_batch_runs.py:436-437`.

## 5. Execution Path / Failure Trace

### Group A

1. Test creates a source and runs ingestion.
2. `IngestionOrchestrator.run_source` receives one new candidate.
3. `_resolve_persisted_tracked_match` finds no persisted job with non-null `tracking_status`.
4. Candidate is added to `transient_ingestion_registry`, not persisted.
5. Test calls JSON `/jobs`; route returns only persisted DB jobs.
6. Empty list causes `json()[0]` `IndexError`.

### Group B

1. Test uses fixture-backed session with schema created in `tests/conftest.py`.
2. Delete endpoint soft-deletes the source using the fixture session.
3. Response background task calls `run_source_delete_cleanup`.
4. Cleanup opens `app.persistence.db.SessionLocal`, not the fixture session/dependency override.
5. With `DATABASE_URL=sqlite+pysqlite:///:memory:`, that session points at a different in-memory DB/connection without the test-created schema.
6. Querying `sources` raises `no such table: sources`.

### Group C

1. Module-level `TestClient(app, raise_server_exceptions=False)` sends requests without the `client` fixture.
2. No test schema is created for app `SessionLocal`; no dependency override is installed.
3. Routes query app DB through normal dependency wiring.
4. Under in-memory `DATABASE_URL`, schema is absent, so requests return 500.

### Group D

1. Test creates a StaticPool in-memory DB fixture session and 12 sources.
2. Batch executor runs up to five worker threads.
3. `build_session_factory_from_session(session)` creates new sessions bound to the same test bind.
4. Multiple worker sessions concurrently call `session.get(Source, ...)` against SQLite in-memory/shared connection state.
5. SQLite raises `InterfaceError: bad parameter or other API misuse` in at least one worker.
6. `_run_source_with_retries` catches the exception, retries, and eventually records source failure(s).
7. Registry marks batch `completed_with_failures`.

## 6. Failure Classification

| Group | Primary classification | QA/product disposition | Severity | Routing |
| --- | --- | --- | --- | --- |
| A: persisted `/jobs` expectations | Test Bug | Stale test expectations after approved feature behavior change | High for CI health; not a product defect | QA test update |
| B: background cleanup `SessionLocal` with in-memory DB | Environment / Configuration Issue | Test infrastructure issue exposed by background task/session boundary | High for CI health | QA test update with backend guidance |
| C: global UI client without fixture DB | Environment / Configuration Issue | Test infrastructure issue; fixture bypass | High for CI health | QA test update |
| D: batch executor threaded SQLite `InterfaceError` | Environment / Configuration Issue | Test infrastructure issue in threaded in-memory SQLite harness | Medium for CI health | QA test update with backend guidance |

## 7. Root Cause Analysis

### Group A: Confirmed Root Cause

Immediate failure point: tests index into an empty JSON `/jobs` list.

Underlying root cause: affected tests encode pre-feature behavior where ingestion persisted all fetched jobs. The current product spec and implementation intentionally keep new untracked ingestion results transient and exclude them from persisted JSON `/jobs`.

Supporting evidence:

- Spec: `docs/product/transient_untracked_ingestion_jobs_product_spec.md:71-79`.
- Implementation: `app/domain/ingestion.py:41-54` and `app/web/routes.py:985-990`.
- Failing assertions/indexing: `tests/integration/test_html_views.py:48`, `tests/integration/test_html_views.py:76`, `tests/ui/test_source_edit_delete_ui_qa.py:74`, `tests/ui/test_source_edit_delete_ui_qa.py:195`.

### Group B: Confirmed Root Cause

Immediate failure point: background cleanup queries `sources` in a DB connection without schema.

Underlying root cause: `run_source_delete_cleanup` opens production `SessionLocal` instead of using the fixture-overridden request session. In-memory SQLite DBs are connection/engine scoped, so the cleanup session does not see `Base.metadata.create_all(engine)` from `tests/conftest.py`.

Supporting evidence:

- Fixture setup: `tests/conftest.py:24-49`.
- Cleanup session path: `app/domain/source_cleanup.py:156-160`.
- Error: `sqlite3.OperationalError: no such table: sources` at `app/domain/source_cleanup.py:42`.

### Group C: Confirmed Root Cause

Immediate failure point: HTML shell tests receive 500 responses.

Underlying root cause: `tests/ui/test_saas_dashboard_ui_revamp.py` creates a module-level client without the repository `client` fixture, so test DB schema and dependency overrides are not applied under in-memory DB configuration.

Supporting evidence:

- Global client: `tests/ui/test_saas_dashboard_ui_revamp.py:7`.
- Fixture it bypasses: `tests/conftest.py:42-49`.
- Observed failures: 500 responses across dashboard/jobs/sources/source-health/tracking endpoints.

### Group D: Most Likely Root Cause

Immediate failure point: batch status is `completed_with_failures` after source worker exceptions.

Underlying root cause: threaded test harness opens multiple sessions against a SQLite in-memory/StaticPool bind derived from one fixture session. Concurrent worker DB reads raise SQLite `InterfaceError`, which the executor records as source failures.

Supporting evidence:

- Test uses threaded executor with shared bind: `tests/unit/test_source_batch_run_qa_validation.py:95-99` and `app/domain/source_batch_runs.py:436-437`.
- Isolated reproduction captured `sqlite3.InterfaceError: bad parameter or other API misuse` at `app/domain/source_batch_runs.py:367`.
- Executor converts worker failures into failed source results and final `completed_with_failures`: `app/domain/source_batch_runs.py:403-420` and `app/domain/source_batch_runs.py:125-130`.

## 8. Confidence Level

High overall.

- Groups A, B, and C are confirmed by direct code paths plus reproduced error messages.
- Group D is high-confidence but labeled “Most Likely” because the failure is concurrency/environment-sensitive; the captured exception directly explains the observed `completed_with_failures`, but production behavior with a non-in-memory DB was not validated here.

## 9. Recommended Fix

### Group A

- Likely owner: QA test update.
- Files: `tests/integration/test_html_views.py`, `tests/ui/test_source_edit_delete_ui_qa.py`, and any helper that seeds a job via ingestion then immediately reads JSON `/jobs`.
- Expected correction: update fixtures to either:
  - track the transient job through `/ingestion/transient-jobs/{id}/tracking-status` before asserting persisted `/jobs`/detail behavior, or
  - assert transient HTML/API behavior where the scenario is intended to cover untracked ingestion results.
- Constraint: do not restore persistence of untracked ingestion jobs; that would violate the feature spec.

### Group B

- Likely owner: QA test update with backend guidance.
- Files: source-delete tests listed above; possible shared fixture support in `tests/conftest.py`.
- Expected correction: ensure background cleanup uses a test-visible session/engine when tests execute under in-memory SQLite. Options include monkeypatching `app.web.routes.run_source_delete_cleanup` for tests that do not validate cleanup, using a file-backed SQLite DB for background-task tests, or introducing an injectable cleanup session factory in test configuration.
- Constraint: production cleanup opening its own `SessionLocal` is appropriate for an async/background task; avoid changing production behavior solely to satisfy in-memory test isolation unless introducing a clean injectable seam.

### Group C

- Likely owner: QA test update.
- File: `tests/ui/test_saas_dashboard_ui_revamp.py`.
- Expected correction: remove module-level `TestClient(app, raise_server_exceptions=False)` and use the repository `client` fixture, or create schema and dependency overrides equivalent to `tests/conftest.py`.

### Group D

- Likely owner: QA test update with backend guidance.
- File: `tests/unit/test_source_batch_run_qa_validation.py`; optionally fixture/session factory helper.
- Expected correction: avoid threaded SQLite in-memory shared-connection misuse. Prefer a file-backed SQLite test DB for this concurrency test, a thread-safe per-worker engine/session factory, or monkeypatch `_run_source_with_retries`/source lookup if the test only intends to validate max concurrency.
- Constraint: do not change `SourceBatchExecutor` retry/failure marking unless a backend reproduction proves the same failure with production-like DB configuration.

## 10. Suggested Validation Steps

After remediation:

1. Re-run targeted feature validation from QA report:
   - `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest tests/unit/test_transient_ingestion_jobs.py tests/api/test_transient_untracked_ingestion_jobs_qa.py tests/integration/test_transient_untracked_cleanup_migration_qa.py tests/ui/test_transient_ingestion_jobs_ui.py tests/ui/test_hide_rejected_job_openings_ui.py`
2. Re-run stale expectation tests after updating their setup:
   - `tests/integration/test_html_views.py`
   - `tests/ui/test_source_edit_delete_ui_qa.py`
3. Re-run source delete/background cleanup tests:
   - `tests/api/test_source_edit_delete_qa.py`
   - `tests/integration/test_api_flow.py::test_source_patch_delete_and_delete_impact_flow`
   - `tests/integration/test_api_flow.py::test_deleted_sources_are_removed_from_html_filters_and_inactive_sources_cannot_run`
   - `tests/integration/test_source_edit_delete_html.py::test_source_delete_html_flow_hides_deleted_source_from_management_surfaces`
4. Re-run UI shell test module after fixture correction:
   - `tests/ui/test_saas_dashboard_ui_revamp.py`
5. Re-run isolated batch concurrency test repeatedly after test-harness correction:
   - `tests/unit/test_source_batch_run_qa_validation.py::test_batch_executor_never_exceeds_five_concurrent_source_runs`
6. Re-run full suite:
   - `DATABASE_URL=sqlite+pysqlite:///:memory: PYTHONPATH=. uv run pytest`

Expected result: full suite green with no restoration of persisted untracked ingestion jobs.

## 11. Open Questions / Missing Evidence

- Why the local full-suite rerun reported 17 failures while QA reported 18: the batch executor failure reproduced reliably in isolation but was not included as failed in the local full-suite summary. This suggests ordering or concurrency sensitivity in that test.
- No production-like file-backed/PostgreSQL run was performed for the batch executor. Needed only if backend wants to rule out a production concurrency defect.

## 12. Final Investigator Decision

Ready for developer fix.

Primary remediation should be routed to QA test updates/test infrastructure, not production feature implementation. No evidence currently requires changing the transient untracked ingestion production behavior.
