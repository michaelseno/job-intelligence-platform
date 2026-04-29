# Bug Report

## 1. Summary
Source Health is accurately showing persisted backend source rows, but the active source data contains invalid/outdated ATS source configurations plus duplicate active sources for the same company/provider. Most reported 404s reproduce directly against the external ATS APIs. One reported Lever failure (`Insider Lever`) is an application parser robustness bug, not an external 404.

## 2. Investigation Context
- Source of report: user/HITL validation on active branch `bugfix/source_health_cleanup`.
- Related workflow: backend source configuration, ingestion, and `/source-health` operations view.
- Environment inspected: configured local `.env` PostgreSQL database `postgresql+psycopg://postgres:postgres@localhost:5432/job_intelligence_platform`; checked-in `job_intelligence_platform.db` is 0 bytes and has no tables.
- Relevant screens/routes: `/source-health`, `/ops/sources`, `/sources`, source batch/manual ingestion.
- Scope: backend/data-ingestion bugfix only unless UI evidence appears.

## 3. Observed Symptoms
- Source Health lists active errored sources with latest health messages such as:
  - `Client error '404 Not Found' for url 'https://api.lever.co/v0/postings/alkami?mode=json'`
  - `Client error '404 Not Found' for url 'https://boards-api.greenhouse.io/v1/boards/notion/jobs'`
  - `Insider Lever`: `'str' object has no attribute 'get'`
  - `HubSpot Greenhouse`: `Source returned zero jobs. Verify whether this is expected.`
- Active healthy duplicate rows exist for the same company/provider, e.g. Asana Greenhouse appears as both `https://job-boards.greenhouse.io/asana` and `https://boards.greenhouse.io/asana`.
- Expected behavior:
  - Invalid external ATS endpoints should not remain active configured sources.
  - Duplicate prevention should allow only one active source per `company + provider`; same company with a different provider is allowed.
  - Parser should handle known Lever payload variants without an opaque `AttributeError`.

## 4. Evidence Collected

### Files/modules inspected
- `app/domain/sources.py`
  - `SourceService.validate()` checks duplicates only by `Source.dedupe_key` (`lines 66-77`).
  - `build_source_dedupe_key()` includes `source_type`, `adapter_key`, normalized `base_url`, and `external_identifier` (`lines 225-228`). This permits duplicate company/provider sources when only `base_url` host differs.
  - `import_csv()` calls the same validation path (`lines 185-222`).
- `app/persistence/models.py`
  - Active unique index is only on `dedupe_key` where `deleted_at IS NULL` (`lines 19-27`).
- `alembic/versions/20260424_0002_sources_soft_delete_schema.py`
  - Migration creates the same active unique index on `dedupe_key` only (`lines 35-42`).
- `app/domain/ingestion.py`
  - Source health is written in `_update_source_health()` from run status and job count (`lines 171-186`). Zero jobs becomes `warning`; failed run becomes `error`.
- `app/domain/operations.py`
  - Source Health lists every non-deleted source ordered by name (`line 14`); no grouping/deduping is performed in query.
- `app/adapters/lever/adapter.py`
  - Fetch URL is constructed as `https://api.lever.co/v0/postings/{external_identifier}?mode=json` (`lines 20-24`).
  - Parser assumes each `lists[].content[]` entry is a dict and calls `entry.get(...)` (`line 30`).
- `app/adapters/greenhouse/adapter.py`
  - Fetch URL is constructed as `https://boards-api.greenhouse.io/v1/boards/{external_identifier}/jobs` (`lines 20-24`).
  - Parser reads `payload.get("jobs", [])` (`line 27`).
- `app/templates/ops/source_health.html` and `app/web/templates/ops/source_health.html`
  - Duplicate template files exist. `app/web/routes.py:64-67` loads `app/templates` before `app/web/templates`, so the active template is `app/templates/ops/source_health.html`. This duplication affects maintainability but is not the ingestion/source duplication root cause.

### Database evidence
- Active duplicate company/provider groups found in PostgreSQL:
  - Asana Greenhouse: ids `66`, `25`
  - Coinbase Greenhouse: ids `21`, `63`
  - Databricks Greenhouse: ids `22`, `64`
  - Discord Greenhouse: ids `68`, `28`
  - Figma Greenhouse: ids `61`, `19`
  - HubSpot Greenhouse: ids `65`, `23`
  - Reddit Greenhouse: ids `67`, `26`
  - Stripe Greenhouse: ids `59`, `17`
- These duplicates differ by `base_url` host (`boards.greenhouse.io` vs `job-boards.greenhouse.io`), creating different `dedupe_key` values despite the same company/provider/external identifier.

### External ATS checks
Direct HTTP checks reproduced the reported external responses:
- Lever 404s returned `404 application/json; charset=utf-8` with body `{"ok":false,"error":"Document not found"}` for `alkami`, `browserstack`, `circleci`, `keepersecurity`, `postman`, `snyk`, `storable`, `subsplash`, and also `insider`.
- Greenhouse 404s returned `404 application/json` with body `{"status":404,"error":"Job not found"}` for `notion` and `plaid`.
- HubSpot Greenhouse returned `200 application/json` with body `{"jobs":[],"meta":{"total":0}}`.
- Insider actual configured slug is `insiderone`, not `insider`; `https://api.lever.co/v0/postings/insiderone?mode=json` returned `200 application/json` with 168 jobs.
- Lever payload shape inspection for `insiderone` showed `lists[].content` can be a string; iterating it yields characters (`'\n'`, `'<'`, `'l'`, ...), which explains `entry.get(...)` failing in `app/adapters/lever/adapter.py:30`.

## 5. Execution Path / Failure Trace
1. A source is created manually or via CSV import through `SourceService.create_source()` / `import_csv()`.
2. Validation builds `dedupe_key = source_type|adapter_key|normalized_base_url|external_identifier`.
3. If the same company/provider/external identifier is entered with a different `base_url`, the dedupe key differs and the active unique index allows the duplicate.
4. Ingestion calls the adapter for the source provider:
   - Lever uses the `external_identifier` as the Lever company slug.
   - Greenhouse uses the `external_identifier` as the Greenhouse board token.
5. HTTP 404s raise via `response.raise_for_status()`, then `IngestionOrchestrator.run_source()` records `run.status='failed'` and source `health_state='error'`.
6. Zero-job successful responses record `run.status='success'`, `jobs_fetched_count=0`, and source `health_state='warning'`.
7. `/source-health` lists all non-deleted sources without grouping, so data duplicates appear as duplicate healthy/warning rows.

## 6. Failure Classification
- Primary classification: **Application Bug** for duplicate prevention and Lever parser robustness.
- Source-specific external 404s: **Data / Fixture Issue** in configured source data, because the external ATS endpoints currently return 404 outside the app.
- HubSpot zero jobs: **Data / Fixture Issue / expected external response**, unless product wants zero-job sources hidden/disabled.
- Severity: **High**. Source Health and batch ingestion are operationally noisy and duplicate active sources can repeatedly ingest the same jobs; however, core app availability is not blocked and no data loss was observed.

## 7. Root Cause Analysis

### Most Likely Root Cause: duplicate active healthy rows
- Immediate failure point: `OperationsService.list_source_health()` returns all non-deleted source rows; duplicates are already present in the database.
- Underlying root cause: active uniqueness is defined by URL-sensitive `dedupe_key`, not by the required business key `company + provider`.
- Supporting evidence:
  - `build_source_dedupe_key()` includes normalized `base_url` (`app/domain/sources.py:225-228`).
  - Unique index is only on `dedupe_key` (`app/persistence/models.py:19-27`).
  - Active duplicates have same company/provider/external identifier but different Greenhouse base hosts.
- UI/query behavior is not the origin; it is surfacing persisted rows as designed.

### Confirmed Root Cause: reported external ATS 404s
- Immediate failure point: `response.raise_for_status()` in Lever/Greenhouse adapters.
- Underlying cause: configured ATS slugs/board tokens currently return 404 directly from external ATS APIs.
- Supporting evidence: direct HTTP checks reproduced the same 404 statuses and provider error bodies.

### Confirmed Root Cause: `Insider Lever` parser error
- Immediate failure point: `entry.get("text", "")` in `app/adapters/lever/adapter.py:30`.
- Underlying cause: Lever `lists[].content` may be a string/HTML blob for `insiderone`, but the parser assumes an iterable of dict entries.
- Supporting evidence: external `insiderone` endpoint returns 200 with 168 jobs; payload shape inspection showed string content entries that reproduce why a string reaches `.get`.

### Confirmed Root Cause: `HubSpot Greenhouse` warning
- Immediate failure point: `_update_source_health()` converts successful zero-job ingestion to `warning` (`app/domain/ingestion.py:178-181`).
- Underlying cause: external Greenhouse endpoint for `hubspot` currently returns a valid 200 response with zero jobs.
- Supporting evidence: direct HTTP response `{"jobs":[],"meta":{"total":0}}`.

## 8. Confidence Level
**High.** The diagnosis is backed by source inspection, active database queries, and direct external ATS response checks. The only uncertainty is whether any uninspected external source list/import file outside this repository originally seeded the duplicate rows.

## 9. Recommended Fix

Likely owner: **dev-backend**.

1. **Duplicate prevention rule**
   - Update `SourceService.validate()` / duplicate lookup to enforce one active source per normalized `company + provider` (`company_name` preferred, fallback to source `name`; provider = `source_type`, possibly plus `adapter_key` for custom providers if product wants that distinction).
   - Keep allowing the same company with different providers, e.g. Keeper Security Greenhouse and Keeper Security Lever are allowed by rule, but invalid Lever should be removed if 404.
   - Add a DB-level protection if feasible: a generated/explicit `company_provider_key` column or equivalent migration-backed unique index where `deleted_at IS NULL`. Python-only validation is not enough for concurrency/import safety.
   - Update tests to cover same company/provider with different base URL as duplicate and same company/different provider as allowed.

2. **Existing duplicate cleanup**
   - Soft-delete or disable duplicate active sources.
   - Follow user rule: keep the most recently successful/healthy source; if neither is healthy, keep the most recent source only if product still wants it monitored.
   - For duplicated Greenhouse healthy sources, suggested retained ids based on current DB evidence:
     - Asana: keep `66`, remove/disable `25`
     - Coinbase: keep `21`, remove/disable `63`
     - Databricks: keep `22`, remove/disable `64`
     - Discord: keep `68`, remove/disable `28`
     - Figma: keep `61`, remove/disable `19`
     - Reddit: keep `67`, remove/disable `26`
     - Stripe: keep `59`, remove/disable `17`
     - HubSpot: if retaining a warning source, keep most recent `65`, remove/disable `23`; consider disabling/removing both if zero jobs is not useful.

3. **External 404 source cleanup**
   - Remove or soft-delete active sources whose ATS endpoint currently returns 404. Do not treat these as HTTP client/code bugs.

4. **Lever parser robustness**
   - In `app/adapters/lever/adapter.py`, normalize `lists` parsing so `group.get("content")` can be either a list of dicts, a list of strings, or a string. Extract text safely and avoid `.get` on non-dicts.
   - Consider adding a clear warning or parser fallback rather than failing the whole source for one unexpected list shape.
   - Add fixture-based unit coverage for `insiderone`/`padsplit`-style Lever list content.

5. **Template/file cleanup (optional, frontend/backend coordination only if desired)**
   - There are duplicate `ops/source_health.html` templates under `app/templates` and `app/web/templates`; active loader order uses `app/templates` first. This is not causing source row duplication, but stale duplicate template files can confuse future changes.

## 10. Suggested Validation Steps
- Backend tests:
  - Creating/importing two Greenhouse sources for the same company/provider with different `base_url` must reject the second source.
  - Creating same company with Greenhouse and Lever must be allowed.
  - Existing deleted sources must not block a new active source under the same company/provider key.
  - Lever adapter parses payloads where `lists[].content` is a string and where it is a list of dicts.
  - HubSpot-style Greenhouse `200 {"jobs":[]}` remains a successful run with warning, unless product changes expected behavior.
- Data validation after cleanup:
  - Query active sources grouped by normalized company/provider; all counts should be `1`.
  - `/source-health` should no longer show duplicate active healthy rows.
  - Removed 404 sources should no longer appear as active Source Health errors.
  - `Insider Lever` should fetch jobs successfully after parser fix, if kept active.

## 11. Open Questions / Missing Evidence
- What import/source list outside the repository created ids `59-77` and the earlier deleted duplicates? No static CSV/seed/source config file containing the reported company names was found in the repository.
- Product should confirm whether HubSpot should be removed because it currently has zero jobs, or kept as a warning source for future openings.
- Product should confirm whether duplicate prevention should normalize company names only by lowercase/whitespace or use stricter slug normalization matching `slugify()`.

## 12. Final Investigator Decision
**Ready for developer fix.** Backend/data-ingestion fixes are sufficient based on current evidence; frontend changes are not required unless the team chooses to remove stale duplicate templates.

## Per-source determination and recommended action

| Source | Current active id(s) | Determination | Evidence | Recommended action |
|---|---:|---|---|---|
| Alkami Technology Lever | 70 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`; DB health message matches. | Remove/soft-delete active source. |
| BrowserStack Lever | 77 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`. | Remove/soft-delete active source. |
| CircleCI Lever | 76 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`. | Remove/soft-delete active source. |
| Keeper Security Lever | 69 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`; separate Greenhouse provider history exists and is allowed by rule. | Remove/soft-delete Lever source only. |
| Postman Lever | 74 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`. | Remove/soft-delete active source. |
| Snyk Lever | 75 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`. | Remove/soft-delete active source. |
| Storable Lever | 72 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`. | Remove/soft-delete active source. |
| Subsplash Lever | 71 | External/source-side 404 / invalid configured source | Direct Lever check returned 404 `Document not found`; same company Greenhouse provider is allowed by rule. | Remove/soft-delete Lever source only. |
| Insider Lever | 73 | App parser bug | Configured slug `insiderone` returns 200 with jobs; Lever parser assumes dict entries and fails on string `lists[].content`. | Fix Lever parser; keep/retry source after fix. Do not remove as 404. |
| Notion Greenhouse | 60 | External/source-side 404 / invalid configured source | Direct Greenhouse check returned 404 `Job not found`. | Remove/soft-delete active source. |
| Plaid Greenhouse | 62 | External/source-side 404 / invalid configured source | Direct Greenhouse check returned 404 `Job not found`. | Remove/soft-delete active source. |
| HubSpot Greenhouse | 23, 65 | Expected external zero jobs + duplicate config | Direct Greenhouse check returned 200 with `jobs: []`; two active same company/provider rows exist. | Remove/disable duplicate; keep id 65 only if monitoring zero-job source is desired, otherwise remove/disable both. |
| Asana Greenhouse | 25, 66 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 66; remove/disable id 25. |
| Coinbase Greenhouse | 21, 63 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 21; remove/disable id 63. |
| Databricks Greenhouse | 22, 64 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 22; remove/disable id 64. |
| Discord Greenhouse | 28, 68 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 68; remove/disable id 28. |
| Figma Greenhouse | 19, 61 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 61; remove/disable id 19. |
| Reddit Greenhouse | 26, 67 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 67; remove/disable id 26. |
| Stripe Greenhouse | 17, 59 | Duplicate config/app uniqueness gap | Same company/provider/external id, different base_url, both healthy. | Keep id 59; remove/disable id 17. |
