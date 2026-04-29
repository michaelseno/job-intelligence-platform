# Test Report

## 1. Execution Summary
- Retest scope: original source-health cleanup, schema guardrail, and 13 newly validated ATS source additions.
- Targeted tests executed: 20
- Targeted passed: 20
- Targeted failed: 0
- Unit + adapter contract regression tests executed: 49
- Unit + adapter contract passed: 49
- Compile check: passed
- Broader API/HTML regression: environment-limited by the expected stale local PostgreSQL schema guardrail.

## 2. Detailed Results
| Test / validation | Outcome | Evidence |
|---|---:|---|
| `PYTHONPATH=. uv run --with-editable . pytest tests/unit/test_schema_guard.py tests/unit/test_sources.py tests/unit/test_source_health_cleanup.py tests/unit/test_source_seed.py tests/adapter_contract/test_lever_adapter.py tests/integration/test_source_health_migrations.py` | Passed | `20 passed, 4 warnings in 1.23s` |
| `PYTHONPATH=. uv run --with-editable . pytest tests/unit tests/adapter_contract` | Passed | `49 passed, 4 warnings in 0.41s` |
| `PYTHONPATH=. uv run --with-editable . python -m compileall app alembic` | Passed | Completed app/Alembic compile traversal without errors. |
| Seed definition inspection | Passed | `VALIDATED_SOURCE_ADDITIONS` contains 13 entries matching the validated list and generated normalized company/provider keys. |
| API/HTML source regression command | Environment-limited / expected guardrail | `1 passed, 24 errors`; TestClient startup fails fast with `DatabaseSchemaOutOfDateError`, current DB revision `20260429_0003`, required head `20260429_0004`, and `alembic upgrade head` instruction. |
| Changed-file scope inspection | Passed | New implementation is backend/domain, Alembic, tests, README/docs. No frontend route/template/static change was required. |

## 3. Failed Tests
No targeted acceptance-criteria tests failed.

### Environment-limited broader regression errors
The broader API/HTML regression suite cannot complete in the current local environment because local PostgreSQL is intentionally behind repository Alembic head after the new source migration:

```text
DatabaseSchemaOutOfDateError: Database schema is out of date for this application version. Run `alembic upgrade head` against the same DATABASE_URL before starting the server. Current DB revision: 20260429_0003; required head revision: 20260429_0004.
```

This is the expected schema guardrail behavior and is not an opaque route-level `UndefinedColumn` failure.

## 4. Failure Classification
| Failure / limitation | Classification | Root cause hypothesis | Severity / impact |
|---|---|---|---|
| Broader TestClient/API/HTML tests blocked at startup | Environment Issue / Expected Guardrail | Local PostgreSQL has not run `20260429_0004_add_validated_sources.py`; guardrail blocks startup until `alembic upgrade head` is applied. | Non-blocking for targeted QA; route-level smoke/regression requires migrating local DB first. |

## 5. Observations
- `app/domain/source_seed.py` defines exactly 13 validated source additions:
  - Point Wild Greenhouse
  - Fundraise Up Greenhouse
  - Shift Technology Greenhouse
  - The Economist Group Greenhouse
  - Tailscale Greenhouse
  - HighLevel Lever
  - Cloaked Lever
  - Drivetrain Lever
  - Celara Lever
  - Fullscript Lever
  - Panopto Lever
  - dLocal Lever
  - Coderio Lever
- Seed logic sets `notes=None`; the user-provided final role/context column is not persisted as source notes/description.
- Seed logic uses both `company_provider_key` and legacy `dedupe_key` lookup and skips active duplicates, preserving one active source per normalized company/provider.
- Migration `20260429_0004_add_validated_sources.py` runs the seed idempotently after `20260429_0003`.
- README now documents that `alembic upgrade head` is required for the source-health cleanup and validated source seed migrations.

## 6. Regression Check
- Original source-health cleanup criteria remain covered by passing tests for confirmed removal, HubSpot removal, duplicate prevention/cleanup, migration/index behavior, schema guardrail, and Lever parser robustness.
- New source-addition criteria are covered by `tests/unit/test_source_seed.py` and migration integration coverage.
- Unit and adapter contract regression suite passed.
- API/HTML regression was attempted but appropriately blocked by the stale local DB guardrail; manual route smoke should be performed after applying `alembic upgrade head` to the local PostgreSQL database.

## 7. QA Decision
Approved. Targeted automated evidence confirms original cleanup behavior, schema guardrail behavior, and idempotent addition of all 13 validated sources without persisting the role/context column. Broader route testing is limited only by the expected stale local DB guardrail and requires operator migration before server smoke testing.

[QA SIGN-OFF APPROVED]
