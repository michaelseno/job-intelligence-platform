# Sources Batch Run Controls Backend Note

## Backend Changes
- Added batch source run preview/start/status support for `Run All` and `Run Selected`.
- Added in-memory preview snapshots and batch state registry with TTL cleanup.
- Added background batch executor with max concurrency 5, max 3 attempts per source, and 1s/2s retry backoff.
- Batch attempts reuse `IngestionOrchestrator.run_source(..., trigger_type="batch_manual")` so single-source `Run now` behavior remains unchanged.

## API / Service Contracts
- `POST /sources/batch-runs/preview`
  - `mode="all"` evaluates all non-deleted system sources and ignores provided source IDs/filter state.
  - `mode="selected"` requires selected source IDs, de-duplicates them, and skips missing/deleted/inactive/unhealthy selections.
- `POST /sources/batch-runs`
  - Starts from an unexpired preview and validates existing job preferences.
  - Returns `202` when execution is scheduled, `200` when zero eligible sources complete immediately, `409` when another batch is active, `404` for unknown previews, and `410` for expired previews.
- `GET /sources/batch-runs/{batch_id}`
  - Returns aggregate progress, skipped sources, per-source status, attempts used, source run IDs, and final summary fields.

## Tests / Checks Run
- `pytest tests/unit/test_source_batch_runs.py tests/api/test_source_batch_run_api.py` failed because `pytest` was not on PATH.
- `python -m pytest tests/unit/test_source_batch_runs.py tests/api/test_source_batch_run_api.py` failed because `python` was not on PATH.
- `python3 -m pytest tests/unit/test_source_batch_runs.py tests/api/test_source_batch_run_api.py` failed because the system Python did not have pytest installed.
- `./.venv/bin/python -m pytest tests/unit/test_source_batch_runs.py tests/api/test_source_batch_run_api.py` passed: `8 passed in 0.10s`.
- `./.venv/bin/python -m pytest` passed: `98 passed in 2.53s`.

## Limitations / Follow-ups
- Batch state is process-local and non-durable by design.
- Multi-process deployments would need a distributed lock/queue to enforce a global single active batch.
- Frontend still needs to wire toolbar controls, confirmation, polling, progress, and summary rendering to these APIs.
