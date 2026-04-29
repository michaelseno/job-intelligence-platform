# Sources Batch Run Controls Frontend Note

## Summary
- Added Sources inventory toolbar controls for `Run All` and `Run Selected`.
- Added visible-row selection checkboxes with select-all-visible behavior and Healthy-selection enablement for `Run Selected`.
- Wired frontend preview/start/status polling to the implemented batch run APIs.
- Added confirmation dialog, inline progress panel, completion summary, skipped-source details, and accessible compact row actions.

## Components / State
- Template hooks live in `app/templates/sources/index.html` under `data-source-batch-root`.
- Controller logic lives in `initSourceBatchRuns()` in `app/static/js/app.js`.
- Client state tracks selected visible IDs, preview loading, active batch status, pending preview, initiating focus target, and polling timer.
- Batch UI uses backend preview/status payloads as authoritative for eligible/skipped counts and per-source results.

## UI Behavior Implemented
- `Run All` posts preview with `mode: "all"` and no filter/search state.
- `Run Selected` posts selected visible row IDs and is enabled only when at least one selected row has `data-health-state="healthy"`.
- Confirmation shows eligible/skipped counts, selected count for selected mode, skipped-source details, and zero-eligible close-only state.
- Confirming starts the batch with stored job preferences, shows progress, polls every 1 second while active, and renders terminal summary.
- Row actions remain Open, Edit source, Run now, and Delete source, now as compact icon controls with `aria-label`/`title`; delete keeps `btn--danger` styling.

## Tests / Checks Run
- `./.venv/bin/python -m pytest tests/integration/test_sources_batch_run_html.py tests/api/test_source_batch_run_api.py tests/unit/test_source_batch_runs.py` — passed (`10 passed`).
- `node --check app/static/js/app.js` — passed.
- `./.venv/bin/python -m pytest` — passed (`100 passed`).

## Limitations / Follow-ups
- Selection is visible-row only; cross-page selection remains out of scope.
- No frontend package script or browser automation command exists in the repo, so validation used server-rendered HTML tests, backend API tests, full pytest, and JavaScript syntax checking.
- Batch history remains in-session/process-local per backend design.
