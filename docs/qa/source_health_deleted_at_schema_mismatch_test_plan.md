# Test Plan

## 1. Feature Overview
Validate the regression fix for the `sources.deleted_at` schema/runtime mismatch that caused `GET /source-health` to fail with HTTP 500 in migration-managed environments.

## 2. Acceptance Criteria Mapping

| AC | Requirement | Planned Coverage |
|---|---|---|
| AC-01 | Alembic upgrades cleanly from `20260423_0001` to `20260424_0002` on PostgreSQL | Live PostgreSQL upgrade on isolated temporary database using local Alembic environment |
| AC-02 | Migration adds `sources.deleted_at` without disturbing existing schema relationships | PostgreSQL schema inspection after upgrade + migration integration regression |
| AC-03 | Active-only dedupe uniqueness matches soft-delete design | PostgreSQL schema inspection of partial unique index predicate + behavioral duplicate/soft-delete validation |
| AC-04 | Foreign keys to `sources.id` remain intact | PostgreSQL inspector validation across `source_runs`, `job_postings`, and `job_source_links` |
| AC-05 | Migrated environments no longer fail on `/source-health` | PostgreSQL-backed `OperationsService` validation + migrated app `TestClient` smoke check |
| AC-06 | Related `/sources` behavior remains intact as practical | PostgreSQL-backed `/sources` smoke check + existing source API/service regression suite |

## 3. Test Scenarios
- Upgrade an isolated PostgreSQL database from `20260423_0001` to `20260424_0002` and verify the revision completes successfully.
- Inspect migrated PostgreSQL schema and confirm `sources.deleted_at` exists.
- Confirm the legacy unconditional constraint is removed and the partial unique index exists with `deleted_at IS NULL` predicate.
- Confirm foreign keys from `source_runs`, `job_postings`, and `job_source_links` still reference `sources.id`.
- Verify an active duplicate `dedupe_key` fails while reuse after soft delete succeeds.
- Verify `OperationsService.list_source_health()` excludes soft-deleted sources after PostgreSQL migration.
- Verify `/source-health`, `/sources`, and `/dashboard` HTML requests return HTTP 200 in a migrated PostgreSQL-backed app session.
- Re-run adjacent source API/service regressions for practical coverage outside the specific migration path.

## 4. Edge Cases
- Database created from pre-fix Alembic revision then upgraded on PostgreSQL.
- Reuse of a `dedupe_key` after soft delete while an active duplicate remains prohibited.
- Soft-deleted source excluded from health/list queries after migration.
- Foreign-key-bearing schema upgraded in place without recreating `sources`.
- HTML route execution against migrated PostgreSQL-backed sessions rather than metadata-created schema only.

## 5. Test Types Covered
- Migration/integration tests
- API/integration regressions
- Domain/service regressions
- PostgreSQL-backed schema validation
- PostgreSQL-backed migrated app smoke validation
