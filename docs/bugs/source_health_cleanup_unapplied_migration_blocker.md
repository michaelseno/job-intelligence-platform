# Bug Report

## 1. Summary
`GET /sources` returns 500 after restarting the server because the running ORM model includes `Source.company_provider_key`, but the local PostgreSQL schema is still at Alembic revision `20260424_0002` and does not contain the `sources.company_provider_key` column added by migration `20260429_0003`.

## 2. Investigation Context
- Source of report: HITL validation blocker after QA sign-off on active branch `bugfix/source_health_cleanup`.
- Related workflow: Sources management page, source-health cleanup migration, local PostgreSQL startup/deployment workflow.
- Branch context: current active correction branch; no new branch should be created.
- Failing route/action: `GET /sources`.
- User-provided call path: `app/web/routes.py:list_sources` -> `build_source_page_context` -> `SourceService.list_sources()` -> SQLAlchemy query.
- User-provided error: `sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedColumn) column sources.company_provider_key does not exist`.

## 3. Observed Symptoms
- Failing workflow: opening `/sources` after restarting the server.
- Exact error summary:
  ```text
  sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedColumn) column sources.company_provider_key does not exist
  Failing query selects sources.company_provider_key from sources
  ```
- Local database inspection confirmed:
  ```text
  alembic_version= 20260424_0002
  has_company_provider_key= False
  ```
- Expected behavior:
  - After deploying/running code with the new ORM model, the target database should be upgraded to Alembic head (`20260429_0003`) before routes query `Source` rows.
  - If migrations are not applied, the app should fail with clearer operational guidance or the runbook should make the required step explicit.

## 4. Evidence Collected
- `app/persistence/models.py`
  - `Source` now maps `company_provider_key` and includes a partial unique index on it (`lines 27-33`, `line 46`).
- `app/domain/sources.py`
  - `SourceService.validate()` queries `Source.company_provider_key` while checking duplicates (`lines 72-80`).
  - `create_source()` and `update_source()` assign `company_provider_key` (`lines 109-114`, `lines 152-157`).
  - `SourceService.list_sources()` selects full `Source` ORM entities, so SQLAlchemy includes every mapped column, including `company_provider_key`.
- `alembic/versions/20260429_0003_source_company_provider_key.py`
  - Adds `sources.company_provider_key` if missing (`lines 24-27`).
  - Runs source-health cleanup/backfill after adding the column (`lines 29-34`).
  - Creates active unique index `ix_sources_company_provider_active_unique` (`lines 36-43`).
- `README.md`
  - Local quick start requires migrations before app start: `alembic upgrade head` (`lines 11-17`).
- `app/main.py`
  - Startup/lifespan configures logging and scheduler only; it does not run migrations or check schema compatibility (`lines 19-28`).
- `app/persistence/db.py`
  - Engine/session are created from settings; no schema validation or migration guard exists (`lines 17-27`).
- `docs/qa/source_health_cleanup_qa_report.md`
  - QA already documented the same risk: local PostgreSQL not upgraded causes `UndefinedColumn: column sources.company_provider_key does not exist` (`lines 15`, `25-35`).
  - QA sign-off explicitly states local/deployed PostgreSQL databases must run Alembic migration `20260429_0003` before using code with the new ORM model (`line 57`).

## 5. Execution Path / Failure Trace
1. Server starts with code from `bugfix/source_health_cleanup`.
2. SQLAlchemy imports `app.persistence.models.Source`, whose mapping includes `company_provider_key`.
3. Local PostgreSQL remains at Alembic revision `20260424_0002`; the `sources` table does not have `company_provider_key`.
4. User requests `/sources`.
5. `app/web/routes.py:list_sources()` renders HTML and calls `build_source_page_context()`.
6. `build_source_page_context()` calls `SourceService.list_sources()`.
7. `list_sources()` executes `select(Source)`, causing SQLAlchemy to select all mapped columns, including `sources.company_provider_key`.
8. PostgreSQL rejects the query with `UndefinedColumn`, producing a 500 response.

## 6. Failure Classification
- Primary classification: **Environment / Configuration Issue**.
- Contributing classification: **Application Bug / Deployment Guardrail Gap** because the app provides no startup/schema compatibility guard and route failure is an opaque 500 instead of a clear migration-required message.
- Severity: **Blocker** for HITL validation in this local environment because `/sources` cannot load until the database is migrated.

## 7. Root Cause Analysis
### Confirmed Root Cause
- Immediate failure point: SQLAlchemy-generated `SELECT` for `Source` includes `sources.company_provider_key`, but PostgreSQL table `sources` lacks that column.
- Underlying root cause: database migrations were not applied after code introduced ORM column `Source.company_provider_key` and Alembic migration `20260429_0003`.
- Supporting evidence:
  - Local DB `alembic_version` is `20260424_0002`.
  - Local `sources` columns do not include `company_provider_key`.
  - Migration `20260429_0003` is the migration that adds the missing column.
  - README local workflow requires `alembic upgrade head` before app start.

### Plausible Contributing Factors
- QA documented the operational risk, but the app does not enforce or surface schema mismatch at startup.
- Existing tests exposed a related local PostgreSQL mismatch through background cleanup using `SessionLocal`, indicating test harness isolation/documentation may need improvement.

## 8. Confidence Level
**High.** The reported traceback, migration file, ORM model, README workflow, QA report, and direct local DB inspection all point to the same missing migration.

## 9. Recommended Fix
Likely owner: **dev-backend**.

Recommended remediation:
1. **No application data/model logic rollback is indicated.** The missing column is expected after the source-health cleanup implementation.
2. **Add clearer migration guardrails.** Implement a lightweight startup or request-time schema/version check that compares DB Alembic revision to code head, then fails fast with an actionable message such as: `Database schema is not current; run alembic upgrade head`.
   - Candidate location: `app/main.py` lifespan or a persistence helper imported during startup.
   - Constraint: do not auto-run migrations in app startup unless explicitly approved; safer local/deployment pattern is fail-fast plus runbook command.
3. **Update documentation/runbook.** Add a branch-specific note to `README.md` or release/implementation docs that after pulling this branch, run `alembic upgrade head` before starting/restarting the app against PostgreSQL.
4. **Improve test harness isolation or skip behavior.** The QA report showed broader tests can hit local PostgreSQL through background cleanup. Add/adjust tests so background tasks use the test session factory or explicitly document that local PostgreSQL must be migrated before running broader source regression tests.
5. **Optionally add a small schema compatibility test.** Verify that ORM mapped columns introduced by migrations are present after `alembic upgrade head`, extending the existing migration integration test coverage if needed.

## 10. Suggested Validation Steps
- Temporary local validation after applying migration:
  - Run Alembic upgrade against the same `DATABASE_URL` used by the server.
  - Confirm `alembic_version` is `20260429_0003` or head.
  - Reload `/sources`; expected result is HTTP 200 and rendered Sources page.
  - Reload `/source-health`; expected result is HTTP 200 and no duplicate/removed source rows from cleanup scope.
- Regression validation for guardrail/doc fix:
  - Start app against an intentionally stale DB and confirm a clear migration-required startup/request error instead of an opaque route traceback.
  - Run source management tests with migrated local PostgreSQL or fully isolated test DB sessions.

## 11. Open Questions / Missing Evidence
- Whether the project wants automatic migration execution on local startup is not specified. Current conventions use manual `alembic upgrade head`.
- Need developer decision on exact guardrail style: fail-fast startup exception, health-check warning, admin banner, or deployment documentation only.

## 12. Final Investigator Decision
**Ready for developer fix.** Immediate unblock is an unapplied migration. A backend follow-up is recommended for clearer guardrails/documentation/tests so the same schema mismatch is caught before HITL users hit a 500.

## Temporary Local Workaround
Clearly labeled workaround, not a code fix:

```bash
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/job_intelligence_platform" .venv/bin/alembic -c alembic.ini upgrade head
```

Then restart/reload the server and retry `GET /sources`.
