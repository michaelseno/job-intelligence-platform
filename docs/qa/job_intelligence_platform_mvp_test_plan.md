# Test Plan

## 1. Feature Overview

The Job Intelligence Platform MVP is a single-user, local-first FastAPI + Jinja web application for onboarding job sources, ingesting jobs from supported adapters, classifying jobs into `matched` / `review` / `rejected`, exposing transparent reasoning, supporting manual keep/save overrides, tracking application progress, generating daily digests and reminders, and surfacing source health.

This QA plan is implementation-ready and aligned to:
- `docs/product/job_intelligence_platform_mvp_product_spec.md`
- `docs/architecture/job_intelligence_platform_mvp_technical_design.md`
- `docs/architecture/job_intelligence_platform_implementation_plan.md`
- `docs/uiux/job_intelligence_platform_mvp_uiux_spec.md`
- `docs/frontend/job_intelligence_platform_frontend_implementation_plan.md`
- `docs/backend/job_intelligence_platform_backend_implementation_plan.md`

Primary workflow under test:

`add source -> ingest jobs -> classify -> view dashboard -> get digest -> track applications`

---

## 2. QA Scope and Objectives

### 2.1 In Scope
- Source onboarding via manual form and CSV import
- Supported source families: Greenhouse, Lever, named common ATS patterns, and approved custom adapters
- Ingestion orchestration, normalization, source attribution, deduplication, update handling, and idempotency
- Classification correctness for `matched`, `review`, `rejected`
- Sponsorship ambiguity defaulting to `review`
- Decision transparency: score, matched rules, rejected rules, evidence snippets, summary rationale
- Dashboard, jobs list/detail, source health, tracking, digest, reminders
- Manual keep/save behavior and tracking state separation from automated bucket
- Source run history, health summaries, warning states, and operational recovery behavior
- End-to-end workflow success in local-first single-user mode

### 2.2 Out of Scope
- Multi-user behavior, authentication, authorization, RBAC
- Public SaaS deployment
- Unsupported ATS vendors or arbitrary unsupported websites
- Performance scaling beyond MVP readiness checks
- Advanced reminder snooze/suppression behavior unless explicitly implemented in MVP

### 2.3 QA Objectives
1. Verify all MVP acceptance criteria are testable and covered.
2. Prove the core workflow succeeds without manual database repair or code intervention.
3. Prevent silent failures in ingestion, classification, notifications, and source health.
4. Validate that automated decisions are explainable, auditable, and do not block user judgment.
5. Establish release-quality gates and regression priorities for implementation.

### 2.4 Quality Risks Driving Test Depth
- Connector fragility for Greenhouse, Lever, common patterns, and custom adapters
- Duplicate/updated jobs causing incorrect counts, stale records, or repeated notifications
- Over-rejection from rules or incorrect sponsorship handling
- Transparency gaps where a bucket is shown without sufficient evidence
- Confusion between automated bucket vs user tracking status
- Digest/reminder logic producing missing, duplicate, stale, or non-actionable items
- Empty-result runs being hidden instead of flagged

### 2.5 Testability Dependencies and Assumptions
The following items must be explicitly defined or locked before implementation-level QA can fully convert this plan into deterministic automated assertions:
- Final named CSV/manual source contract, including source-type-specific required fields
- Final allowlist of supported `common_pattern` variants
- Final allowlist of approved custom adapters for MVP
- Digest time-window definition and run schedule
- Reminder threshold defaults and reminder timing semantics
- Stale/removed job thresholds and empty-result anomaly thresholds
- Evidence policy for low-text jobs and for inferred rules when direct text snippets are unavailable

Until those items are finalized, QA can prepare fixture structure and scenario coverage, but some expected outcomes must remain conditional rather than hard-coded.

---

## 3. Acceptance Criteria Mapping

### 3.1 Source Management

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| SM-01 | User can add a source via manual form and see it listed as active | P0 | UI, integration, E2E |
| SM-02 | User can upload a valid CSV and create sources from rows | P0 | UI, integration, E2E |
| SM-03 | Invalid/incomplete source input is clearly flagged and does not create broken sources silently | P0 | unit, integration, UI |
| SM-04 | Source record shows source type and health summary | P0 | integration, UI |
| SM-05 | Duplicate source onboarding is prevented or clearly warned | P1 | integration, UI |
| SM-06 | Unsupported direct pages are not presented as supported | P0 | unit, integration, UI/manual |

### 3.2 Ingestion, Normalization, Attribution, Deduplication

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| IN-01 | Jobs fetched from supported source types appear in normalized application format | P0 | adapter contract, integration, E2E |
| IN-02 | Each job is linked to the source that produced it | P0 | integration |
| IN-03 | Title, source/company context, URL/reference, and reviewable text content are available after ingestion | P0 | integration, UI |
| IN-04 | Every ingestion run persists run history and result metrics | P0 | integration |
| IN-05 | Duplicate jobs across repeated runs do not create duplicate canonical jobs | P0 | integration |
| IN-06 | Duplicate jobs across multiple sources preserve provenance correctly | P0 | integration |
| IN-07 | Updated upstream jobs refresh canonical state without losing history | P0 | integration |
| IN-08 | Empty-result runs are treated as warning conditions when unexpected/repeated | P0 | integration, UI |
| IN-09 | Failed source runs do not block healthy source runs | P0 | integration, E2E |

### 3.3 Classification and Transparency

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| CL-01 | Every ingested job is classified into `matched`, `review`, or `rejected` | P0 | unit, integration, E2E |
| CL-02 | Every classified job displays final score and reasons contributing to decision | P0 | integration, UI |
| CL-03 | At least one evidence snippet is shown for each supported rule-based conclusion when source text allows | P0 | unit, integration, UI |
| CL-04 | Explicit mismatch conditions can drive rejection when rules support it | P0 | unit, integration |
| CL-05 | Unclear or missing sponsorship defaults to `review`, not `rejected` | P0 | unit, integration, E2E |
| CL-06 | Manual save/keep does not erase automated classification or explanation | P0 | integration, UI, E2E |
| CL-07 | Decision history is preserved across reclassification/version changes | P1 | integration |

### 3.4 Dashboard, Review, and Detail UX

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| UI-01 | Landing dashboard shows summary views for matched, review, rejected | P0 | UI, E2E |
| UI-02 | User can open job detail and inspect transparency data | P0 | UI, E2E |
| UI-03 | User can identify newly relevant jobs without visiting each source | P0 | UI/manual, E2E |
| UI-04 | UI clearly separates bucket, tracking status, and source health | P0 | UI/manual |
| UI-05 | Empty, loading, success, and error states are understandable | P1 | UI/manual |

### 3.5 Manual Override and Tracking

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| TR-01 | User can save a rejected or review job | P0 | UI, integration, E2E |
| TR-02 | Saved jobs remain visible for later action and reminders | P0 | integration, UI, E2E |
| TR-03 | User can assign/update statuses: saved, applied, interview, rejected, offer | P0 | UI, integration, E2E |
| TR-04 | Classification bucket and tracking status coexist without ambiguity | P0 | UI, integration |
| TR-05 | Tracked jobs remain visible even if source later fails or job disappears upstream | P0 | integration, UI/manual |

### 3.6 Digest and Reminders

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| NT-01 | Daily digest contains only new matched and review jobs for digest period | P0 | integration, E2E |
| NT-02 | Saved jobs with no action appear in reminders when threshold is met | P0 | integration, E2E |
| NT-03 | Applied jobs needing follow-up appear in reminders when threshold is met | P0 | integration, E2E |
| NT-04 | Notification content is actionable and links back to review/tracking workflow | P1 | UI/manual |
| NT-05 | Jobs are not re-digested or re-reminded incorrectly because of idempotency issues | P0 | integration |
| NT-06 | Reminder dismiss/snooze behavior matches final MVP decision and does not alter tracking/classification state | P1 | integration, UI/manual |

### 3.7 Source Health and Operations

| ID | Acceptance Criterion | Priority | Test Coverage |
|---|---|---:|---|
| OP-01 | Each source exposes last run, success/failure, jobs fetched, and empty-result warnings | P0 | integration, UI |
| OP-02 | Failed runs are visibly distinguishable from successful runs | P0 | UI, integration |
| OP-03 | Repeated empty-result conditions are surfaced as warnings | P0 | integration, UI |
| OP-04 | Stale/broken sources are diagnosable without raw logs | P1 | UI/manual |
| OP-05 | Manual triggers are available for scheduled actions where required | P1 | UI/manual, integration |
| OP-06 | Empty-result, stale, and failure states follow explicitly defined thresholds rather than implicit heuristics | P1 | integration |

---

## 4. Test Strategy by Layer

### 4.1 Unit Tests

Purpose: fast validation of deterministic business logic.

Primary focus areas:
- Source validation rules for manual and CSV input
- CSV row parsing and required/optional field validation
- Adapter config validators
- Canonical normalization helpers
- Deduplication key generation and merge rules
- Classification rule engine scoring and bucket assignment
- Sponsorship ambiguity override logic
- Evidence extraction for title, description, location, sponsorship text
- Digest inclusion logic for “new matched” and “new review”
- Reminder eligibility logic for saved inactivity and applied follow-up
- Reminder dismiss/snooze state handling if included in MVP
- Health state computation for healthy/warning/error/stale

Minimum unit coverage goals:
- 100% of P0 rule branches for classification and reminders
- All adapter config validators
- All empty-result and failure-state health transitions

### 4.2 Integration Tests

Purpose: validate service and persistence behavior across modules and database.

Primary focus areas:
- Manual source create -> persisted source -> health summary projection
- CSV import -> row validation -> created/skipped/duplicate results
- Adapter fetch -> normalization -> canonical persistence -> source/job link creation
- Repeat ingestion idempotency
- Cross-source duplicate merge behavior
- Updated upstream job re-ingestion behavior
- Source run history, counts, warning/error summaries
- Classification decision persistence and rule detail persistence
- Tracking event history and current tracking projection
- Digest generation persistence and item uniqueness
- Reminder generation persistence and current state rules

### 4.3 Adapter Contract Tests

Purpose: ensure all supported adapters behave consistently against the shared contract.

Required for:
- Greenhouse
- Lever
- Each MVP common ATS pattern
- Each approved custom adapter

Contract assertions:
- Valid config accepted; invalid config rejected with actionable errors
- Adapter returns normalized candidate fields required by downstream workflow
- Structured warning/error reporting is stable
- Source attribution fields are present
- Sparse or partial upstream data is handled predictably
- Empty result is distinguishable from fetch failure

### 4.4 UI / Manual Validation

Purpose: verify server-rendered workflow behavior, clarity, accessibility, and page-state correctness.

Primary focus areas:
- Source form validation messaging
- CSV import feedback and row-level errors
- Dashboard information hierarchy and separation of concepts
- Job detail transparency readability
- Clear labeling of text-supported evidence vs inferred reasoning
- Save/keep and tracking actions from list and detail pages
- Source health warning visibility and action guidance
- Digest/reminders readability and actionability
- Empty states, error banners, stale data messaging
- Keyboard navigation, semantic labels, focus visibility, accessible status cues

### 4.5 End-to-End Tests

Purpose: validate the complete MVP success path and critical failure paths through the application surface.

Critical E2E flows:
1. Manual source onboarding -> run ingestion -> classify -> dashboard review -> save job -> update status
2. CSV onboarding -> run ingestion for multiple sources -> verify dashboard and source health
3. Ambiguous sponsorship job -> lands in `review` -> user saves -> reminder later appears
4. New matched/review jobs -> digest generation -> digest displays only newly eligible jobs
5. Applied job -> follow-up threshold reached -> reminder appears
6. One source fails while another succeeds -> source health reflects both correctly
7. Manual trigger path for digest/reminders -> output matches scheduled-path domain rules

### 4.6 Non-Functional MVP Checks

These are release checks, not full performance/security programs.

- Basic performance: acceptable local page response for dashboard/jobs pages under MVP-sized dataset
- Basic resilience: failed connector does not corrupt persisted state or block healthy runs
- Basic security hygiene: CSV upload validation, HTML content sanitization/escaping, no unsafe rendering of source content, localhost-only assumptions preserved

---

## 5. Test Scenarios

### 5.1 Source Onboarding

#### Happy Path
- Create Greenhouse source manually with valid token/URL.
- Create Lever source manually with valid company identifier.
- Import mixed valid CSV rows covering Greenhouse, Lever, common pattern, custom adapter.
- Imported sources appear in configured source list with correct type labels.

#### Validation / Negative
- Missing required fields by source type.
- Invalid source type or unsupported adapter key.
- Malformed URL/base URL.
- CSV missing required columns.
- CSV row with unsupported direct source marked as supported.
- Duplicate rows in the same CSV.
- CSV import repeated with existing sources.

#### Edge Cases
- Optional fields omitted where allowed.
- Mixed valid and invalid rows in one CSV import.
- Whitespace/case normalization in source identifiers.
- Duplicate source created once manually and once via CSV.

### 5.2 Ingestion and Normalization

#### Happy Path
- Greenhouse source returns multiple jobs with complete fields.
- Lever source returns multiple jobs with complete fields.
- Common-pattern adapter returns jobs with expected structure.
- Custom adapter returns jobs with expected structure.

#### Validation / Negative
- Adapter config valid at create time but upstream fetch fails.
- Unsupported direct page selected.
- Partial payload missing expected fields.
- Timeout/network error during run.
- Empty result due to true no-openings case.
- Empty result due to parser regression/failure.

#### Edge Cases
- Same job appears twice in same source payload.
- Same role appears across two sources with overlapping text and different URLs.
- Existing job updated upstream after first ingestion.
- Job removed upstream after being tracked.
- Sparse description text with limited evidence support.

### 5.3 Classification and Transparency

#### Happy Path
- Strong role match + remote + acceptable sponsorship evidence => `matched`.
- Strong role match + Spain location => `matched` or `review` per scoring rules, with transparent reasons.
- Explicit mismatch (wrong role family / incompatible location / explicit no sponsorship) => `rejected`.

#### Validation / Negative
- Missing score or missing rules for classified job.
- Bucket shown without evidence when source text supports evidence.
- Sponsorship ambiguous but classified as `rejected`.
- Manual keep overwrites or hides original decision.

#### Edge Cases
- Contradictory sponsorship language in one posting.
- Strong role fit but location missing.
- Strong role fit but sponsorship missing.
- Weak evidence support due to minimal text.
- Inferred rule conclusion shown without direct text snippet must be labeled as inference, not presented as quoted evidence.
- Multiple negative and positive rules causing borderline score.

### 5.4 Dashboard and Review UX

#### Happy Path
- Dashboard shows counts and recent jobs by bucket.
- Job detail displays score, reasons, evidence, source metadata.
- Jobs list supports bucket, tracking, source, and text filters.
- Save/keep and update tracking actions available from list and detail views.

#### Validation / Negative
- Mislabeling or visual confusion between bucket and tracking badge.
- Filter state lost after action redirect.
- Empty dashboard after successful ingestion due to projection failure.
- Failed source presented as “healthy”.

#### Edge Cases
- No jobs yet.
- Filters produce zero results.
- Job marked removed/stale but still tracked.
- Mobile/tablet layouts for key actions and statuses.

### 5.5 Tracking Workflow

#### Happy Path
- Save untracked job -> tracking becomes `saved`.
- Update saved -> applied -> interview.
- Update to rejected or offer from tracking flow.

#### Validation / Negative
- Invalid tracking status rejected.
- Tracking update modifies automated bucket.
- Saved job disappears from reminders/tracking page unexpectedly.

#### Edge Cases
- Save already-saved job.
- Update tracked job while source is stale/failed.
- Rejected automated job manually saved then later applied.

### 5.6 Digest and Reminders

#### Happy Path
- Generate digest after ingestion; includes new `matched` and `review` only.
- Generate saved-job inactivity reminder after threshold.
- Generate applied-job follow-up reminder after threshold.

#### Validation / Negative
- Old jobs repeated in new digest without qualifying state change.
- `rejected` jobs included in digest.
- Saved job reminder generated before threshold.
- Reminder generated for job already progressed beyond eligible status.
- Reminder dismissal or snooze mutates tracking status or automated bucket.

#### Edge Cases
- Multiple ingestions in one digest period.
- Job bucket changes between digest runs.
- Job saved after digest generated but before reminder run.
- No eligible jobs for digest/reminder.
- Digest or reminder output generated correctly by manual trigger and by scheduled trigger using same eligibility rules.

### 5.7 Source Health and Operations

#### Happy Path
- Successful run updates last run, status, count, healthy state.
- Failed run updates failure state and preserves diagnostics.
- Repeated empty results move source to warning state.

#### Validation / Negative
- Run failure hides prior successful data.
- Empty-result parser regression not flagged.
- One failing source blocks run history updates for other sources.
- Source state changes with undocumented thresholds, making warning behavior non-deterministic.

#### Edge Cases
- First-ever run returns zero jobs.
- Stale source with no recent successful runs.
- Partial success if supported by implementation.

---

## 6. Edge Cases

- Source configured correctly but legitimately has zero openings.
- Source returns zero because parser broke or page structure changed.
- Direct ATS page partially matches a supported pattern but lacks required fields.
- Ambiguous, missing, or contradictory sponsorship language.
- Strong role match with sparse text and weak evidence snippets.
- Duplicate source onboarding across manual + CSV flows.
- Duplicate jobs across multiple sources or different URLs.
- Job updated upstream after initial classification.
- Job removed upstream after being saved/applied.
- Reminder threshold met for a job user intends to ignore temporarily.
- Re-ingestion of same payload multiple times.
- Digest generation after no new jobs.
- Failed source run followed by recovery run.

---

## 7. Source / Adapter Validation Strategy

### 7.1 Adapter Inventory Coverage
Each supported adapter must have:
- config validation tests
- fixture-based parsing tests
- normalization tests
- contract tests
- at least one end-to-end or integration path through ingestion

### 7.2 Required Adapter Test Dimensions
- Valid source config
- Invalid source config
- Upstream success with complete data
- Upstream success with partial/sparse data
- Legitimate zero-result response
- Upstream failure / timeout / malformed response
- Unsupported or changed structure behavior

### 7.3 Adapter Exit Criteria
An adapter is MVP-ready only if:
- it produces required canonical fields for downstream classification/review
- it emits actionable failures and warnings
- it does not silently create empty success where parsing failed
- it passes repeat-run idempotency checks

### 7.4 Common Pattern and Custom Adapter Risk Handling
- Common-pattern adapters receive higher regression focus because structural drift is likely.
- Custom adapters must be locked to approved named sources and tested against curated fixtures.
- Unsupported direct pages must fail clearly with non-supported messaging, not degrade into false success.

---

## 8. Data Integrity and Idempotency Checks

### 8.1 Source Integrity
- No broken source records from invalid manual/CSV input
- Duplicate source prevention or warning is deterministic
- Source type and adapter key remain stable after creation

### 8.2 Run Integrity
- Each ingestion attempt creates one persisted run record
- Run status transitions are consistent: `running -> success/partial_success/failed`
- Run counts sum logically across created/updated/unchanged/error totals

### 8.3 Job Integrity
- Canonical jobs are unique by dedupe strategy
- `job_source_links` preserve provenance for each contributing source
- Repeated ingestion of unchanged jobs does not duplicate records
- Upstream updates modify current projections without destroying history
- Tracked jobs remain accessible even when upstream source later removes them

### 8.4 Decision Integrity
- Exactly one current automated decision per current decision version/projection
- Historical decisions remain queryable/auditable
- Manual keep/save does not mutate historical automated decision data
- Decision rule rows remain linked to the correct decision record

### 8.5 Notification Integrity
- Digest includes each qualifying job once per digest period/channel
- Reminder generation is idempotent within the same eligibility window
- Notification generation does not regress tracking state or job bucket

---

## 9. Classification Transparency Verification

QA must verify, for each representative bucketed job:
- bucket is shown
- final score is shown
- matched rules are shown when applicable
- rejected/negative rules are shown when applicable
- evidence snippet is present for each rule where source text supports it
- evidence snippet corresponds to actual source content field
- sponsorship ambiguity receives explicit special-handling note/callout when relevant
- manual keep/save preserves transparency data unchanged

Representative transparency test set:
- clear matched job with strong evidence
- ambiguous sponsorship job sent to review
- explicit rejection with negative evidence
- sparse-text job with limited evidence and graceful fallback messaging

Failure conditions considered blocking:
- missing bucket or score
- sponsorship ambiguity routed to `rejected`
- transparency panel contradicts stored bucket
- evidence snippets fabricated, unrelated, or absent despite available text

---

## 10. Reminder and Digest Verification

### 10.1 Daily Digest Checks
- Generated on expected schedule or manual trigger
- Includes only jobs newly classified into eligible buckets during digest window
- Excludes `rejected` jobs
- Excludes previously digested unchanged jobs
- Displays actionable summary and navigation back to job detail/tracking
- Uses the in-app digest view as the required MVP verification surface

### 10.2 Reminder Checks
- Saved-job reminders fire only after saved inactivity threshold
- Applied-job reminders fire only after follow-up threshold
- Reminder eligibility stops when tracking status changes out of relevant state
- Reminder output remains actionable and not system-log-oriented
- Manual keep/save affects reminders only by creating/retaining tracking state, not by changing automated classification

### 10.3 Notification Regression Checks
- Re-running digest/reminder generation without new eligibility does not duplicate output
- Ingestion update that changes bucket/status updates future eligibility correctly
- Manual keep/save impacts reminder eligibility only through tracking rules, not by rewriting automated classification

---

## 11. Source Health and Operational Testing

### 11.1 Health State Coverage
- Healthy: recent successful run with expected data
- Warning: repeated or unexpected zero-result run
- Error/Failed: latest run failed
- Stale: no recent successful run within expected freshness window
- Partial data: run succeeded with weak/incomplete fields, if implemented

### 11.2 Operational Scenarios
- Manual source run from UI
- Scheduled-equivalent run reflected in same run history model
- Connector timeout captured as failed run
- Healthy source unaffected by another source failure
- Recovery after previous failure resets health appropriately

### 11.3 Operational Usability Checks
- User can distinguish broken vs empty vs stale sources without raw logs
- Last run timestamp, status, count, and warning explanation are visible
- Next actions or guidance are understandable

---

## 12. Risk-Based Prioritization

### 12.1 P0 Blocking Test Areas
- Manual source creation
- CSV source import validation
- Greenhouse and Lever ingestion
- Supported common/custom adapter contract validity
- Canonical job persistence and source attribution
- Deduplication and idempotent re-ingestion
- Bucket assignment for all jobs
- Sponsorship ambiguity -> `review`
- Transparency completeness: score, rules, evidence
- Manual keep/save without classification loss
- Tracking status lifecycle
- Daily digest for new `matched` + `review`
- Reminders for saved inactivity and applied follow-up
- Source health required fields and empty-result warnings
- Full end-to-end workflow

### 12.2 P1 High-Value Regression Areas
- Duplicate source warnings
- Stale source behavior
- Sparse-text transparency fallbacks
- Filter persistence and list/detail action ergonomics
- Cross-source duplicate merge behavior
- Job removed upstream after tracking
- Recovery from failed sources

### 12.3 P2 Deferred / Lower-Risk Areas
- Optional export/email notification channels
- Richer sorting/filtering polish
- Non-critical visual polish and metadata formatting

---

## 13. Test Data Recommendations

### 13.1 Core Fixture Set
Prepare reusable fixtures for:
- Greenhouse source with 3-5 jobs
- Lever source with 3-5 jobs
- At least one supported common-pattern source
- Each approved custom adapter

### 13.2 Canonical Job Content Matrix
Include postings that cover:
- strong Python backend remote match
- strong QA automation / SDET match
- Spain-based role with acceptable fit
- explicit no-sponsorship language
- ambiguous sponsorship language
- missing sponsorship language
- poor role fit but manually worth saving
- sparse description text
- updated job content across later run
- same job duplicated across sources

### 13.3 CSV Fixture Matrix
- all-valid rows
- mixed valid/invalid rows
- duplicate rows
- unsupported source rows
- malformed URL / missing required field rows
- whitespace/case normalization cases
- conditionally required `external_identifier` missing
- missing `adapter_key` for `common_pattern` / `custom_adapter`
- valid duplicates against already-existing sources (create-only import should skip)

### 13.4 Notification Data Set
- newly matched jobs within digest window
- newly review jobs within digest window
- previously digested jobs outside current eligibility
- saved jobs just below and just above inactivity threshold
- applied jobs just below and just above follow-up threshold

### 13.5 Operational Data Set
- healthy source history
- repeated empty-result history
- failed run history
- stale source history
- recovery run after failure

---

## 14. Test Types Covered

- Unit tests
- Integration tests
- Adapter contract tests
- UI functional tests
- Manual UX/accessibility checks
- End-to-end workflow tests
- Basic performance/reliability checks
- Basic security/input-handling checks

---

## 15. Regression Priorities and Release Quality Gates

### 15.1 Regression Suite Structure

#### Smoke Suite (run on every change affecting MVP flow)
- app loads dashboard
- manual source create
- CSV import valid file
- Greenhouse ingestion happy path
- Lever ingestion happy path
- classification of representative matched/review/rejected jobs
- save/keep action
- tracking update action
- digest generation
- reminder generation
- source health page load

#### Core Regression Suite
- all P0 scenarios
- adapter contract suite for all supported adapters
- dedupe/idempotency scenarios
- failure-path source health scenarios
- representative UI state/error scenarios

#### Extended Regression Suite
- all P1 scenarios
- sparse/contradictory data edge cases
- recovery and stale-source scenarios
- basic performance and security checks

### 15.2 Release Quality Gates
Implementation is not release-ready unless all are true:

1. **P0 pass rate:** 100% of P0 automated and required manual checks pass.
2. **No blocking defects:** no open defects that break source onboarding, ingestion, classification, dashboard review, digest, reminders, tracking, or source health.
3. **Adapter readiness:** all claimed MVP adapters pass contract and integration tests.
4. **Data integrity:** no duplicate canonical job creation on repeat-run tests; no loss of tracking/manual keep state.
5. **Transparency completeness:** representative jobs in all three buckets show score, rule reasons, and evidence behavior per spec.
6. **Notification correctness:** digest/reminder idempotency and eligibility logic verified.
7. **Operational visibility:** failed and empty-result runs visibly surface in source health.
8. **End-to-end success:** complete user workflow passes in local environment.

### 15.3 Exit Decision Guidance
- **APPROVED:** all P0 tests pass, no blocking defects, no unresolved data integrity or transparency defects.
- **CONDITIONAL APPROVAL:** only non-blocking P1 issues remain with documented workarounds.
- **REJECTED:** any P0 failure, missing critical coverage, or unresolved blocker in core workflow.

---

## 16. Implementation Readiness Notes for QA Execution

- Prefer fixture-driven automated coverage for adapters and classification rules.
- Use deterministic timestamps in tests for digest/reminder eligibility.
- Preserve separate assertions for automated bucket vs tracking status in every relevant test.
- Record expected run-count deltas for repeated ingestion to catch hidden duplication bugs.
- Treat unsupported direct pages and parser regressions as explicit negative tests, not incidental failures.
- Include manual UX review for dashboard clarity because acceptance criteria rely on understandable transparency and operational visibility, not only raw data presence.
- Before implementation starts, convert all open timing/threshold/allowlist decisions into versioned QA fixtures so automation expectations stay stable across docs and code.
