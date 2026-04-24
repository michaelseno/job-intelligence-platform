# Job Intelligence Platform MVP Technical Design

## Feature Overview
The Job Intelligence Platform MVP is a single-user, local/self-hosted web application that ingests jobs from configured hiring sources, normalizes and deduplicates them, classifies them into `matched`, `review`, or `rejected`, exposes transparent decision evidence, supports manual save/keep overrides, and helps the user track applications, reminders, daily digests, and source health.

The MVP is intentionally designed around a monolithic FastAPI application with server-rendered Jinja views, PostgreSQL persistence, and an internal background job execution layer that works locally first but can evolve cleanly to AWS-managed workers later.

## Product Requirements Summary
- Single-user local/self-hosted deployment for MVP.
- FastAPI + Jinja web application.
- PostgreSQL from day one.
- No authentication in local MVP.
- Sources: Greenhouse, Lever, common ATS/direct page patterns, and 3-5 custom adapters.
- Source onboarding via CSV upload and manual form.
- Automated buckets: `matched`, `review`, `rejected`.
- Sponsorship ambiguity must default to `review`.
- Transparent scoring and evidence for every classification.
- Manual override/keep required without removing automated decision history.
- Tracking statuses: `saved`, `applied`, `interview`, `rejected`, `offer`.
- Daily digest for new matched and review jobs.
- Reminder flows for saved and applied jobs.
- Source health and operations UI required.
- End-to-end workflow: add source -> ingest -> classify -> dashboard -> digest -> track applications.

## Scope

### In Scope
- Single FastAPI application serving UI, APIs, scheduling, and background execution.
- Source CRUD, CSV import, validation, and source health views.
- Connector abstraction for ATS and custom adapters.
- Ingestion, normalization, deduplication, classification, and persistence.
- Dashboard, job detail, source operations, application tracking, digest/reminder views.
- Local notification generation and display/export.
- Operational logging, run history, and basic health indicators.

### Out of Scope
- Multi-user tenancy, authN/authZ, or RBAC.
- Generic crawler framework for arbitrary unsupported sites.
- ML-based ranking/recommendation models.
- Automatic application submission.
- Cloud-native AWS deployment implementation in MVP.
- Real-time websockets or push infrastructure.

## Architecture Overview

### System Context
Primary actors and systems:
- **User**: configures sources, reviews jobs, updates tracking, monitors source health.
- **FastAPI App**: serves Jinja pages, JSON endpoints, orchestrates domain workflows.
- **PostgreSQL**: system of record for sources, jobs, runs, decisions, evidence, tracking, reminders.
- **Background Job Runner**: executes ingestion, classification, digest, and reminder jobs.
- **External Job Sources**: Greenhouse, Lever, common ATS pages, custom company adapters.
- **Notification Output**: MVP should support at minimum in-app digest/reminder views and optional local email/file output via configuration.

### Architectural Style
- **Modular monolith** for MVP simplicity and local operability.
- Clear internal boundaries by domain module so services can later split if AWS scaling is needed.
- **Synchronous UI requests** for user-driven actions; **asynchronous background jobs** for ingestion, classification, digest generation, and reminder generation.
- **Database-first persistence** with explicit run records and auditability.

### High-Level Flow
1. User creates/imports sources.
2. Scheduler or manual action triggers an ingestion run.
3. Source adapter fetches raw job payloads.
4. Normalization maps external payloads to canonical job schema.
5. Deduplication resolves new vs existing jobs across sources.
6. Classification engine scores and buckets jobs; evidence is stored.
7. Dashboard and job detail views read canonical job + latest decision + user tracking state.
8. Daily digest and reminder jobs materialize actionable outputs.
9. Source ops UI surfaces run status, counts, warnings, and failures.

## System Components

### 1. Web Application Layer
Responsibilities:
- Serve dashboard, source management, job detail, tracking, digest, and ops pages.
- Accept source form submissions and CSV uploads.
- Expose internal JSON endpoints for progressive enhancement where useful.
- Trigger manual ingestion runs and classification re-runs.

### 2. Source Management Module
Responsibilities:
- Persist source definitions.
- Validate manual and CSV input.
- Distinguish standard adapters vs custom adapters.
- Store source configuration, activation status, health summary, and warnings.

### 3. Connector / Adapter Framework
Responsibilities:
- Provide a consistent interface for all source types.
- Encapsulate fetch logic, parsing, normalization hints, and source-specific validation.
- Isolate brittle parsing logic from the rest of the application.

Proposed adapter categories:
- `greenhouse`
- `lever`
- `common_pattern` (subtyped by supported pattern)
- `custom_adapter` (named custom implementation)

Core adapter contract:
- Validate source config.
- Fetch job list or job pages.
- Return normalized candidate records plus fetch metadata.
- Emit structured errors/warnings.
- Expose adapter capabilities and expected source fields.

### 4. Ingestion Orchestrator
Responsibilities:
- Create source run records.
- Invoke adapters.
- Handle retries/timeouts/error capture.
- Pass fetched jobs into normalization and deduplication pipeline.
- Update source health summary and run metrics.

### 5. Normalization and Deduplication Module
Responsibilities:
- Convert source-specific payloads into canonical internal schema.
- Preserve raw source payload snapshot for debugging/audit.
- Create stable fingerprints for duplicate detection.
- Identify updates to previously seen jobs.

### 6. Classification Engine
Responsibilities:
- Evaluate explicit rules against canonical job content.
- Produce score, bucket, matched rules, rejected/negative rules, and evidence snippets.
- Apply sponsorship ambiguity override to `review`.
- Persist immutable decision records so manual actions do not overwrite automated classification history.

### 7. Tracking and Workflow Module
Responsibilities:
- Manage user tracking status separately from automated bucket.
- Support save/keep action independent of bucket.
- Support reminders and digest inclusion logic.

### 8. Scheduling and Background Execution Module
Responsibilities:
- Run periodic ingestion, digest, and reminder jobs locally.
- Support manual triggers from UI.
- Track job execution state and logs.
- Remain replaceable with AWS scheduler/queue workers later.

### 9. Operations and Observability Module
Responsibilities:
- Surface source health, run history, empty-result warnings, and failure diagnostics.
- Emit structured logs.
- Store operational metrics at application level sufficient for single-user diagnosis.

## Data Models and Storage Design

### Storage Strategy
- **PostgreSQL** is the system of record for all persistent state.
- Store both canonical structured fields and selected raw payload snapshots/HTML excerpts for explainability and debugging.
- Prefer append-only records for run history and classification decisions; use current-state summary columns for fast UI reads.

### Key Entities

#### `sources`
Represents configured job sources.

Key fields:
- `id`
- `name`
- `source_type` (`greenhouse`, `lever`, `common_pattern`, `custom_adapter`)
- `adapter_key` (for pattern/custom variants)
- `company_name`
- `base_url`
- `external_identifier` (board token/company slug when relevant)
- `config_json` (source-specific settings)
- `is_active`
- `created_at`, `updated_at`
- `last_run_at`
- `last_run_status`
- `last_jobs_fetched_count`
- `consecutive_empty_runs`
- `health_state` (`healthy`, `warning`, `error`)
- `health_message`

Constraints:
- Unique index on normalized combination of `source_type + adapter_key + base_url/external_identifier` where possible.
- Soft prevention of duplicate CSV/manual source onboarding with user-visible duplicate warning.

### Source Input Contract

#### Manual Source Creation
Minimum required fields by source family:
- `name`
- `source_type`
- `base_url`
- `external_identifier` for source families that require a board/company locator
- `adapter_key` for `common_pattern` and `custom_adapter`

Optional fields:
- `company_name`
- `is_active`
- `notes`
- source-specific `config_json` values only when required by the selected adapter

#### CSV Import Contract
MVP baseline CSV columns:
- `name` (required)
- `source_type` (required)
- `base_url` (required)
- `external_identifier` (conditionally required)
- `adapter_key` (required for `common_pattern` / `custom_adapter`)
- `company_name` (optional)
- `is_active` (optional, default `true`)
- `notes` (optional)

CSV import behavior:
- Create-only for MVP; duplicate rows or existing-source matches are reported as skipped, not updated in place.
- Mixed valid/invalid rows are allowed; valid rows are imported and invalid rows are reported with row-specific errors.
- Import result summary must report `created`, `skipped_duplicate`, and `invalid` counts.

#### `source_runs`
Represents each ingestion attempt for a source.

Key fields:
- `id`
- `source_id`
- `trigger_type` (`manual`, `scheduled`, `csv_import_validation`, future `api`)
- `status` (`running`, `success`, `partial_success`, `failed`)
- `started_at`, `finished_at`
- `jobs_fetched_count`
- `jobs_created_count`
- `jobs_updated_count`
- `jobs_unchanged_count`
- `error_count`
- `warning_count`
- `empty_result_flag`
- `log_summary`
- `error_details_json`

#### `job_postings`
Canonical job entity.

Key fields:
- `id`
- `canonical_key` (dedupe key)
- `primary_source_id`
- `title`
- `company_name`
- `job_url`
- `location_text`
- `employment_type`
- `remote_type`
- `description_text`
- `description_html` (optional)
- `sponsorship_text`
- `posted_at`
- `first_seen_at`
- `last_seen_at`
- `last_ingested_at`
- `current_state` (`active`, `stale`, `removed`)
- `latest_bucket`
- `latest_score`
- `latest_decision_id`
- `manual_keep` (boolean summary flag)
- `tracking_status` (nullable summary field for fast reads)

Notes:
- Keep latest decision summary on job row for dashboard performance, but authoritative history lives in decision tables.

#### `job_source_links`
Maps one canonical job to one or more contributing sources.

Key fields:
- `id`
- `job_posting_id`
- `source_id`
- `source_run_id`
- `external_job_id`
- `source_job_url`
- `raw_payload_json`
- `content_hash`
- `is_primary`
- `first_seen_at`, `last_seen_at`

Purpose:
- Preserve many-to-one relation for duplicates across sources.
- Support provenance and debugging.

#### `job_decisions`
Automated classification outputs.

Key fields:
- `id`
- `job_posting_id`
- `decision_version`
- `bucket` (`matched`, `review`, `rejected`)
- `final_score`
- `sponsorship_state` (`supported`, `unsupported`, `ambiguous`, `missing`)
- `decision_reason_summary`
- `created_at`
- `is_current`

#### `job_decision_rules`
Rule-level detail for each decision.

Key fields:
- `id`
- `job_decision_id`
- `rule_key`
- `rule_category` (`role_positive`, `role_negative`, `location_positive`, `location_negative`, `sponsorship`, `seniority`, other future)
- `outcome` (`matched`, `negative`, `override`, `informational`)
- `score_delta`
- `evidence_snippet`
- `evidence_field` (`title`, `description_text`, `location_text`, etc.)
- `explanation_text`

#### `job_tracking_events`
Tracks user workflow state history.

Key fields:
- `id`
- `job_posting_id`
- `event_type` (`save`, `status_change`, `note`, `reminder_snooze_future`)
- `tracking_status`
- `note_text` (optional)
- `created_at`

#### `digests`
Stores generated daily digest outputs.

Key fields:
- `id`
- `digest_date`
- `status`
- `generated_at`
- `delivery_channel` (`in_app`, `file`, `email`)
- `content_summary`

#### `digest_items`
- `id`
- `digest_id`
- `job_posting_id`
- `bucket`
- `reason` (`new_matched`, `new_review`)

#### `reminders`
Stores reminder outputs.

Key fields:
- `id`
- `job_posting_id`
- `reminder_type` (`saved_follow_up`, `applied_follow_up`)
- `due_at`
- `status` (`pending`, `shown`, `dismissed`, `completed`, future `snoozed`)
- `generated_at`

### Normalization Design
Canonical normalized fields should include:
- job identity: title, company, URL, external ID
- display fields: location, remote status, employment type
- classifier fields: full text, sponsorship-related text, title tokens, location tokens
- provenance fields: source type, adapter, raw payload hash, first/last seen timestamps

Normalization rules:
- Normalize whitespace and HTML to plain text for classification.
- Preserve original URL and a normalized URL for dedupe comparisons.
- Infer remote flags from explicit source fields first, then text heuristics.
- Preserve missing/unknown as explicit null/unknown states, not implied negatives.

### Deduplication Design
Deduplication goal: merge the same job seen from multiple sources while retaining provenance.

Recommended layered strategy:
1. **Strong match**: exact external job ID within same ATS/source family.
2. **URL match**: normalized canonical job URL match.
3. **Fingerprint match**: normalized company + normalized title + location + description hash prefix.
4. **Near-duplicate review heuristic**: only for future phases; do not auto-merge aggressively in MVP.

MVP behavior:
- Auto-merge only on strong match / URL match / high-confidence fingerprint.
- Otherwise keep separate records and mark as possible duplicate for later enhancement if needed.

### Stale/Removed Job Handling
- If a previously seen job is absent from a current run, do not immediately mark removed.
- After configurable threshold of consecutive misses, mark `stale`.
- If source explicitly indicates removal or repeated confirmed absence exceeds threshold, mark `removed`.
- Saved/applied jobs remain visible even if stale/removed.

## API Contracts

### UI Pattern Assumption
The application is primarily server-rendered with Jinja templates. JSON endpoints exist for form submissions, CSV validation previews, and progressive enhancement, but the UI does not require a separate SPA.

### Route / Endpoint Groups

#### Source Management
- `GET /sources` - list configured sources and health summary.
- `GET /sources/new` - manual source form.
- `POST /sources` - create source from form input.
- `GET /sources/import` - CSV upload page.
- `POST /sources/import` - upload and process CSV.
- `POST /sources/{source_id}/run` - trigger manual ingestion run.
- `GET /sources/{source_id}` - source detail and run history.

Request/response expectations:
- Manual form requires at minimum `name`, `source_type`, adapter locator fields.
- CSV response should report created, skipped duplicate, and invalid rows.
- Manual run trigger should create a run record and return updated status view.

#### Jobs / Dashboard
- `GET /` - dashboard landing view.
- `GET /jobs` - list/filter jobs by bucket, tracking status, source, recency.
- `GET /jobs/{job_id}` - job detail with evidence and history.
- `POST /jobs/{job_id}/keep` - set manual keep/save intent.
- `POST /jobs/{job_id}/tracking-status` - update tracking status.

#### Operations
- `GET /ops/sources` - source health overview.
- `GET /ops/runs` - recent ingestion runs.
- `GET /ops/runs/{run_id}` - run detail.

#### Digest / Reminders
- `GET /digest/latest` - latest generated digest.
- `GET /reminders` - current reminders view.
- `POST /reminders/{id}/dismiss` - dismiss reminder.

### API Contract Notes
- HTML responses are first-class; JSON responses should mirror domain objects only where needed.
- For AWS evolution, domain service interfaces should not depend on FastAPI request objects.
- UI forms should submit ids and user intent only; business rules remain server-side.
- CSV import should return row-level outcomes, not only a binary success/failure result.

## Frontend / Client Impact

### Rendering Approach
- Jinja-rendered HTML with minimal JavaScript enhancement.
- Suitable for local-first simplicity and faster end-to-end implementation.

### Core Views
- Dashboard
- Jobs list filtered by bucket/status
- Job detail with transparency section
- Sources list/manage page
- Source import page
- Source operations/health page
- Digest page
- Reminders page

### UI Responsibilities
- Present bucket, score, evidence, and manual keep state clearly.
- Distinguish automated bucket from tracking status.
- Show source health using human-readable warnings, not raw logs.
- Allow manual ingestion trigger and quick diagnosis of failing sources.

### Boundary Assumptions
- Client does not execute classification logic.
- Client does not perform source parsing or deduplication.
- Client may use lightweight JS for filter persistence, upload progress, or inline form handling, but all authoritative state changes are server-driven.

## Backend Logic / Service Behavior

### Source Adapter Strategy and Connector Abstraction
Each adapter implementation should provide:
- `validate_config` behavior
- `fetch_jobs` behavior
- optional `fetch_job_detail` behavior where list endpoints lack full content
- `normalize_candidate` mapping hints
- structured warnings/errors

Adapter design principles:
- Prefer stable public endpoints where available.
- Avoid embedding classification logic in adapters.
- Keep common parsing helpers in shared utilities for pattern-based adapters.
- Represent unsupported or partially supported sources explicitly rather than failing silently.

Recommended adapter substructure:
- Standard connectors: Greenhouse, Lever.
- Common pattern connectors: known board/list/detail HTML structures.
- Custom connectors: one module per company/target source.

### Ingestion Pipeline Design
Per-source ingestion flow:
1. Validate source config.
2. Create `source_run` with status `running`.
3. Fetch jobs with timeout and retry policy.
4. Parse and normalize raw results.
5. Upsert canonical jobs + source links.
6. Mark created/updated/unchanged counts.
7. Run classification for affected jobs.
8. Compute empty-result warning semantics.
9. Finalize run status and refresh source health summary.

Failure behavior:
- Adapter failure should fail only that source run, not the whole application.
- Batch/scheduled ingestion across many sources should continue per source.
- Partial fetch/parsing success should record `partial_success` where possible.

### Supported Source Scope Boundary
- `greenhouse` and `lever` are first-class MVP connectors.
- `common_pattern` support must be implemented as an explicit allowlist of named adapter keys.
- `custom_adapter` support is limited to the approved 3-5 hand-picked targets.
- Unsupported direct/company pages must fail validation as unsupported rather than being accepted as a generic scrape target.

### Rules / Scoring / Evidence Design
MVP should use a deterministic rules engine.

Rule families:
- **Role alignment positive**: Python backend, SDET, QA automation, test infrastructure, developer productivity.
- **Role mismatch negative**: clearly unrelated roles.
- **Location positive**: global remote, remote, Spain-based.
- **Location negative**: clearly incompatible on-site geography when explicit.
- **Sponsorship**: supported / ambiguous / missing / explicitly incompatible.
- **Quality/confidence modifiers**: low-text-content, unclear role, missing critical fields.

Bucketing model recommendation:
- Start with additive score model plus hard guardrails.
- Example behavior model:
  - strong positive role + acceptable location + no explicit sponsorship conflict -> `matched`
  - ambiguous sponsorship or incomplete location with otherwise relevant role -> `review`
  - explicit mismatch conditions with sufficient evidence -> `rejected`

Important product rule:
- If sponsorship is ambiguous or missing, job cannot be rejected on sponsorship grounds alone; default path is `review`.

Evidence generation approach:
- For each triggered rule, persist a short evidence snippet from title, location, or description.
- If direct textual evidence is unavailable, rule may still be recorded as inferred, but UI should clearly distinguish supported evidence vs inference.
- MVP should require at least one evidence snippet for strong positive/negative text-based rules when source text exists.

Decision persistence rules:
- Store each automated evaluation as a separate decision row.
- Current bucket is a projection of latest decision, not overwritten by manual tracking changes.

### Manual Override Behavior
- `manual_keep` indicates the user wants to retain/monitor the job regardless of automated bucket.
- Manual keep does not change the automated bucket; it changes workflow visibility and reminder eligibility.
- Tracking status updates are independent and may coexist with any bucket.
- If a job has no current tracking status, manual keep/save should initialize tracking status to `saved`.
- If a job already has a tracking status, manual keep/save must not overwrite it.
- Reminder eligibility must be computed from tracking status and workflow timestamps; `manual_keep` alone is not a reminder type.

### Scheduling / Job Execution Approach

#### Local-First MVP
Recommended approach:
- In-process scheduler for cron-like tasks.
- Database-backed job execution records.
- Background execution via FastAPI app startup-managed scheduler and worker threads/processes acceptable for MVP.
- One active app instance is the assumed MVP runtime model.

Scheduled task categories:
- Daily source ingestion sweep.
- Daily digest generation.
- Daily reminder generation.
- Optional source health refresh/reconciliation.

Execution assumptions:
- Digest and reminder generation must also be manually triggerable.
- Digest delivery channel for MVP is `in_app`.
- Optional `file` or `email` delivery may reuse the same persisted records later, but is not required for MVP.
- Reminder snooze is not required in MVP; dismissal is sufficient.

Design constraint:
- Scheduling module must be isolated behind interfaces so it can later move to managed scheduling + queue workers in AWS.

#### AWS-Ready Evolution
Target replacement path:
- Scheduler -> EventBridge / cron equivalent.
- Background executor -> SQS + worker service / ECS task / Lambda where appropriate.
- App remains FastAPI UI/API layer.
- PostgreSQL maps to RDS.

This requires:
- idempotent ingestion and classification jobs.
- explicit job/run state persisted in DB.
- no reliance on in-memory only scheduler state.

### Configuration Design
Use layered configuration:
- application settings file / environment variables
- source-level config in DB
- rule configuration in versioned static config files or DB-backed seed data

MVP config domains:
- database connection
- scheduler enablement and run times
- default reminder thresholds
- digest delivery mode
- adapter timeouts / user agents
- stale/removed detection thresholds

### Error Handling Design
- All adapter exceptions must map to structured run errors.
- User-facing source health should summarize failures in plain language.
- CSV import errors must be row-specific and non-silent.
- Parsing anomalies should produce warnings even when run is technically successful.
- Empty results should be warning-level when source historically returns jobs and suddenly returns zero.

### Source Health Design
Health evaluation should consider:
- latest run status
- time since last successful run
- latest jobs fetched count
- consecutive empty runs
- parse warning/error counts

Suggested health states:
- `healthy`: recent successful run with expected behavior
- `warning`: empty result anomaly, stale success, partial parsing concerns
- `error`: failed latest run or repeated failures

## File / Module Structure
Recommended repository/application structure for implementation:

```text
app/
  main.py
  config/
  web/
    routes/
    templates/
    forms/
    view_models/
  domain/
    sources/
    ingestion/
    jobs/
    classification/
    tracking/
    notifications/
    operations/
  adapters/
    base/
    greenhouse/
    lever/
    common_patterns/
    custom/
  persistence/
    models/
    repositories/
    migrations/
  scheduler/
  services/
  observability/
tests/
  unit/
  integration/
  adapter_contract/
  end_to_end/
docs/
  architecture/
```

Module boundary guidance:
- `web` handles HTTP and template rendering only.
- `domain` contains business rules and orchestration contracts.
- `adapters` contains external source integrations.
- `persistence` contains DB models and repositories.
- `scheduler` contains periodic execution and background task orchestration.

## Security and Access Control
- No auth required for local MVP by explicit product decision.
- App should bind to localhost by default to avoid accidental exposure.
- If non-local binding is enabled, show explicit warning in configuration docs.
- Sanitize all scraped HTML before rendering; prefer plain-text rendering for job descriptions in MVP.
- Validate and constrain CSV uploads.
- Use parameterized DB access through ORM/query layer.
- Prevent server-side request abuse by limiting adapter target domains to configured source patterns where practical.

AWS-ready note:
- Future hosted deployment should add auth, CSRF review, session management, secret management, and per-environment network controls.

## Reliability / Operational Considerations
- Make ingestion idempotent using stable dedupe keys and upsert semantics.
- Persist run history for diagnosis.
- Continue processing other sources when one source fails.
- Use configurable request timeout, retry count, and backoff per adapter.
- Protect scheduler from overlapping runs with per-source lock or DB advisory lock.
- Expose last successful run and stale warnings in UI.
- Keep manual actions and tracking history even when sources disappear or jobs are removed.

## Dependencies and Constraints

### External Dependencies
- Greenhouse and Lever accessibility and HTML/API stability.
- Stability of supported common direct ATS patterns.
- Availability of hand-picked custom adapter target pages.
- Local notification delivery mechanism selected for MVP.

### Internal Constraints
- Single-user only.
- Local-first operability.
- Explainable, deterministic decisions preferred over broader opaque coverage.
- Simple architecture favored over distributed services.

## Assumptions
- A modular monolith is sufficient for MVP throughput and complexity.
- Daily digest and reminders are surfaced in-app for MVP, with optional local email/file export deferred.
- Rule configuration can initially live in code-adjacent config/seed data rather than full admin UI.
- Supported common ATS patterns will be a named allowlist, not open-ended scraping.
- Manual keep/save maps to a durable workflow flag and initializes tracking status `saved` only when no tracking status exists yet.
- Dashboard performance is acceptable with summary fields and straightforward indexing in PostgreSQL.
- Baseline CSV schema is the source input contract for MVP implementation unless explicitly revised.
- CSV import is create-only in MVP.
- Scheduler runs in-process with persisted run state and manual trigger parity.

## Risks / Open Questions

### Risks
- Direct/company page variability may make common pattern support brittle.
- Sponsorship language ambiguity may reduce precision and inflate `review` volume.
- Overly aggressive dedupe could merge distinct roles; overly conservative dedupe could clutter dashboard.
- Local scheduler reliability depends on app uptime.
- Some sources may require detail-page fetches, increasing run time and parsing fragility.

### Open Questions
- Final list of supported `common_pattern` variants.
- Final list of 3-5 custom adapters.
- Reminder timing defaults for saved inactivity and applied follow-up.

## Implementation Notes for Downstream Agents
- Implement the product as a modular monolith; do not prematurely split services.
- Treat source adapters as replaceable units behind a shared contract and contract tests.
- Persist raw source payloads/HTML excerpts needed for debugging and evidence generation.
- Keep classification deterministic, explainable, and versioned.
- Separate automated decision history from user workflow state at both schema and service layers.
- Build source operations UI as a first-class MVP surface, not an afterthought.
- Make all scheduled flows manually triggerable from UI/admin routes for local development and validation.
- Design repositories/services around idempotent re-runs so AWS job workers can later reuse the same logic.
- Optimize for correctness and traceability before connector breadth.
- Prefer plain-language user-facing health/error messages derived from structured internal errors.
