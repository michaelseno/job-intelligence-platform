# Test Plan

## 1. Feature Overview

Feature: Hide Rejected Job Openings

The main Jobs display and dashboard actionable job summaries must exclude jobs whose current/latest classification is explicitly `rejected`, while preserving visibility for `matched`, `review`, `NULL`, and unknown non-rejected statuses where they otherwise satisfy existing visibility, search, sort, source, tracking, and bucket filters.

Primary upstream artifacts:
- Product Spec: `docs/product/hide_rejected_job_openings_product_spec.md`
- Technical Design: `docs/architecture/hide_rejected_job_openings_technical_design.md`
- UI/UX Spec: `docs/uiux/hide_rejected_job_openings_uiux_spec.md`

Primary behavior under test:
- `/jobs` HTML and JSON/API-equivalent results exclude rejected jobs at the query/data layer.
- `/jobs?bucket=rejected` returns an empty/no-results state and does not reveal rejected jobs.
- Dashboard actionable counts and matched/review previews exclude rejected jobs.
- Direct `/jobs/{job_id}` access remains unchanged for rejected jobs unless existing source-delete visibility rules hide the job.
- Rejected jobs remain persisted and are not reclassified or deleted by this feature.
- The Jobs bucket selector no longer exposes `Rejected`; preferred all option label is `All actionable`.

## 2. Acceptance Criteria Mapping

| AC | Requirement | Planned Coverage |
|---|---|---|
| AC-01 | Rejected jobs are not shown in the main job openings display. | Unit predicate tests; API `/jobs` tests; HTML/UI list tests asserting no rejected rows/cards/badges. |
| AC-02 | `review` jobs remain visible when they satisfy existing filters. | API, integration, and UI list tests with mixed `review`/`rejected` data. |
| AC-03 | `matched` jobs remain visible when they satisfy existing filters. | API, integration, dashboard, and UI tests with mixed `matched`/`rejected` data. |
| AC-04 | Main-display result totals/counts include only eligible non-rejected jobs. | Dashboard count tests; Jobs results-summary tests where present; JSON response length assertions. |
| AC-05 | Filtering occurs before pagination so pages are filled with eligible jobs. | Design-level regression test if pagination exists; otherwise unit/query test asserting main-display predicate is applied before any future count/limit path and document current no-pagination behavior. |
| AC-06 | Search matching only rejected jobs shows normal empty state and no rejected result. | API search test and HTML empty-state/UI test using a unique rejected-only title/company term. |
| AC-07 | Existing filters do not reintroduce rejected jobs; eligible jobs remain visible. | API/integration matrix for bucket, tracking status, source, search, sort; UI filter tests. |
| AC-08 | A visible `review` job reclassified to `rejected` disappears after persistence and refresh/reload. | Integration/API transition test updating latest/current classification, then reloading `/jobs` and dashboard. |
| AC-09 | A hidden `rejected` job reclassified to `review` or `matched` appears after persistence and refresh/reload if otherwise eligible. | Integration/API transition tests for `rejected -> review` and `rejected -> matched`. |
| AC-10 | Hidden rejected jobs remain in storage unless another cleanup feature deletes them. | Persistence assertions after `/jobs`, dashboard, and bucket-filter requests; verify `job_postings` and decisions unchanged. |
| AC-11 | All-rejected datasets show normal no-results/no-jobs empty state, not an error. | HTML/UI empty-state test and API empty-list test. |
| AC-12 | List/count telemetry, if present, uses filtered visible set or distinguishes stored totals. | Unit/integration test or log/event assertion where telemetry hooks exist; otherwise QA observation confirming no telemetry path implemented. |

Additional explicit technical/UI requirements:

| Requirement | Planned Coverage |
|---|---|
| `NULL` classification remains visible for MVP. | Unit predicate and `/jobs` API tests with `latest_bucket = NULL`. |
| Unknown non-`rejected` classification remains visible for backward compatibility. | Unit predicate and `/jobs` API tests with `latest_bucket = "unknown"` or equivalent. |
| `/jobs?bucket=rejected` must not reveal rejected jobs. | API and HTML/UI tests for direct bookmarked/stale URL. |
| Direct rejected detail route is unchanged. | API/HTML detail test confirms rejected job detail returns existing success behavior when source-visible, and existing 404 behavior for source-hidden/deleted jobs. |
| Dashboard actionable summaries/previews exclude rejected jobs. | Dashboard API/HTML tests for matched/review counts, rejected count `0` or omitted per contract, and preview-card contents. |
| Jobs bucket selector excludes Rejected. | HTML/UI tests for select options and accessible label. |
| Rejected jobs are not deleted or reclassified. | DB assertions before/after list/dashboard access and filter requests. |

## 3. Test Scenarios

### 3.1 Test Data Needs

Create deterministic fixtures with unique titles/company/source values so search/filter assertions are unambiguous:

| Fixture | `latest_bucket` | Current/decision state | Source state | Tracking | Expected `/jobs` default visibility |
|---|---|---|---|---|---|
| `qa_matched_actionable` | `matched` | current latest decision matched | active source | none | Visible |
| `qa_review_actionable` | `review` | current latest decision review | active source | none | Visible |
| `qa_rejected_hidden` | `rejected` | current latest decision rejected | active source | none | Hidden |
| `qa_null_bucket_visible` | `NULL` | no current bucket/decision optional | active source | none | Visible per technical design |
| `qa_unknown_bucket_visible` | non-`rejected` unknown value | latest unknown/nonstandard bucket | active source | none | Visible per technical design |
| `qa_rejected_tracked_hidden` | `rejected` | current rejected | active source | tracked/saved | Hidden from main Jobs and dashboard actionable surfaces |
| `qa_rejected_deleted_source` | `rejected` | current rejected | deleted/hidden source | any | Hidden; direct detail follows existing source-delete behavior |
| `qa_matched_deleted_source_retained` | `matched` | current matched | deleted source with existing retention behavior | active/current state where applicable | Visible only if existing source-delete visibility permits |

Data setup must preserve original classification rows and denormalized fields so tests can verify this feature does not mutate or delete records.

### 3.2 Backend Unit Tests

Recommended files:
- `tests/unit/test_job_visibility.py`
- Add focused tests to existing route/query unit tests if present.

Coverage:
1. Main-display/actionable visibility predicate composes existing source-delete visibility with status filtering.
2. Predicate excludes only explicit `latest_bucket == "rejected"`.
3. Predicate includes `matched`, `review`, `NULL`, and unknown non-rejected buckets.
4. Predicate handles SQL `NULL` correctly with an explicit `IS NULL` branch, not only `!= "rejected"`.
5. Predicate preserves existing deleted-source visibility rules.
6. `apply_main_display_jobs()` or equivalent helper does not mutate `JobPosting.latest_bucket`, `latest_decision_id`, or `JobDecision` rows.
7. Route query construction for `/jobs` and dashboard uses main-display helper; detail/mutation routes continue using existing visibility helper only.
8. If telemetry/count helper exists, counts are derived from the filtered main-display set.

### 3.3 Backend API / Integration Tests

Recommended files:
- `tests/api/test_hide_rejected_job_openings_api.py`
- `tests/integration/test_hide_rejected_job_openings_surfaces.py`

Coverage:
1. `GET /jobs` returns `matched`, `review`, `NULL`, and unknown non-rejected jobs; excludes `rejected` jobs.
2. `GET /jobs?bucket=matched` returns matched jobs only and excludes rejected jobs.
3. `GET /jobs?bucket=review` returns review jobs only and excludes rejected jobs.
4. `GET /jobs?bucket=rejected` returns an empty list/no-results response and no rejected job payloads.
5. `GET /jobs?search=<rejected-only-term>` returns empty/no-results and no rejected payloads.
6. `GET /jobs?search=<shared-term>` returns only eligible non-rejected matches when both rejected and non-rejected jobs match.
7. Existing source, tracking, sort, and combined filters operate only within the non-rejected result set.
8. Dashboard endpoint/page uses filtered actionable data: matched/review counts exclude rejected jobs; rejected count is `0` or omitted per implementation contract; previews contain no rejected jobs.
9. Direct `GET /jobs/{rejected_job_id}` remains accessible for a source-visible rejected job if that was existing behavior.
10. Direct `GET /jobs/{source_hidden_rejected_job_id}` follows existing source-delete not-found behavior.
11. Reclassification `review -> rejected` removes the job from `/jobs` and dashboard after persisted update and reload.
12. Reclassification `rejected -> review` and `rejected -> matched` makes the job visible after persisted update and reload when all other filters match.
13. Rejected jobs remain present in normal persistence mechanisms after list/dashboard requests; no unintended delete/archive/reclassification occurs.
14. All-rejected dataset returns empty `/jobs` and dashboard actionable counts/previews without server error.

### 3.4 Frontend / UI Tests

Recommended file:
- `tests/ui/test_hide_rejected_job_openings_ui.py`

Coverage:
1. Jobs page default load renders only non-rejected table rows/cards.
2. No rejected badge, rejected row/card, `.row-muted`, or `.job-card-muted` appears on `/jobs` for rejected fixture data.
3. Bucket select contains only actionable options: all/default (`All actionable` preferred), `Matched`, and `Review`.
4. Bucket select does not contain visible, hidden, disabled, or selected `Rejected` option.
5. Stale/bookmarked `/jobs?bucket=rejected` shows normal empty state and the select visually falls back to the default actionable option.
6. Results summary, if present, matches rendered non-rejected result count and does not imply total stored jobs include rejected entries.
7. Empty state appears when all matching jobs are rejected and uses non-error copy.
8. Search/filter form retains accessible labels and keyboard tab order after removing the rejected option.
9. Dashboard matched/review stat cards and preview sections exclude rejected jobs; no clickable rejected dashboard card routes to `/jobs?bucket=rejected` unless retained as non-actionable contract fallback with value `0`.
10. Direct rejected detail page can still show rejected status badge if existing detail behavior allows access.
11. Responsive smoke checks verify desktop table and mobile card layouts both omit rejected jobs.

### 3.5 Regression Tests

Recommended regression scope:
1. Existing source-delete visibility tests: ensure main-display rejected filtering composes with retained/hidden deleted-source rules.
2. Existing jobs filters/search/sort tests: update expectations so rejected fixtures are no longer returned by main Jobs display.
3. Existing dashboard tests: update counts/previews to actionable-only semantics.
4. Existing classification flow tests: ensure classification still writes `job_decisions` and denormalized latest fields as before; only list visibility changes.
5. Existing notifications/reminders/digest tests: confirm this feature does not silently alter out-of-scope reminder/tracking surfaces unless they intentionally reuse dashboard/main-display query.
6. Existing detail route tests: confirm rejected detail access did not regress.
7. Existing template tests for duplicate paths (`app/templates` and `app/web/templates`) if both are active or covered.

### 3.6 Basic Security, Privacy, and Reliability Checks

1. Confirm this feature is not treated as access control: rejected job detail remains governed by existing source-delete/detail visibility only.
2. Confirm list/dashboard responses do not leak hidden rejected job titles/descriptions in rendered HTML, JSON payloads, data attributes, or dashboard previews.
3. Confirm telemetry/log assertions, if implemented, do not log sensitive job title/description content and distinguish visible actionable counts from stored totals.
4. Confirm no destructive mutation is triggered by list/dashboard access.
5. Confirm stale query parameters (`bucket=rejected`, invalid bucket values if supported) fail closed for rejected visibility and do not produce stack traces.

## 4. Edge Cases

| Edge Case | Expected Result | Coverage |
|---|---|---|
| All jobs are rejected. | `/jobs` empty state; dashboard actionable counts/previews empty/zero; no error language. | API + UI empty-state tests. |
| Underlying first page or first query batch contains rejected jobs before eligible jobs. | Eligible jobs fill the displayed page/list where pagination exists; no short/empty page due only to UI hiding. | Pagination regression if available; otherwise query-layer predicate unit/integration assertion. |
| Job has `NULL` classification. | Visible by default per technical design. | Unit + API + UI fixture. |
| Job has unknown non-`rejected` classification. | Visible by default per technical design/backward compatibility. | Unit + API fixture. |
| Multiple classification records disagree. | Current/latest display classification (`latest_bucket`) controls visibility. | Integration fixture with historical rejected/current matched and historical matched/current rejected. |
| Search term matches only rejected jobs. | Empty/no-results state; no rejected data leaked. | API + HTML/UI search tests. |
| Source/tracking/company/location filters match rejected and non-rejected jobs. | Only eligible non-rejected jobs shown. | API/integration filter matrix. |
| User manually requests `/jobs?bucket=rejected`. | Empty/no-results; no rejected option selected or exposed in UI. | API + UI bookmarked URL test. |
| Rejected job is tracked/saved/has reminders. | Hidden from Jobs and dashboard actionable surfaces; out-of-scope reminder/tracking surfaces unchanged unless shared query. | Integration + regression tests. |
| Rejected job direct detail URL. | Behavior unchanged; accessible if existing source visibility allows, 404 if existing rules hide it. | Detail route tests. |
| Reclassification while user has page open. | Current page may remain stale; refresh/reload reflects persisted classification. | Integration transition tests. |
| Duplicate template paths. | Active and tested template variants do not expose `Rejected` option. | HTML/template regression tests. |

## 5. Test Types Covered

- Functional correctness: main Jobs filtering, dashboard filtering, direct detail unchanged, no record mutation.
- Validation and negative scenarios: stale `bucket=rejected`, rejected-only search/filter results, invalid/stale filters where supported.
- Edge cases: all-rejected data, `NULL`/unknown buckets, multiple classification records, tracked rejected jobs, deleted-source composition.
- API/UI consistency: JSON/API and server-rendered Jobs/Dashboard surfaces apply the same visibility rule.
- Integration/regression: classification transitions, source-delete visibility composition, dashboard previews/counts, template option removal.
- Basic reliability: query-layer filtering before counts/pagination where applicable; refresh/reload semantics after persisted classification changes.
- Basic security/privacy: no hidden rejected payloads in main list/dashboard output; no sensitive telemetry/log expansion; no destructive side effects.

Recommended commands once tests are implemented:

```bash
pytest tests/unit/test_job_visibility.py
pytest tests/api/test_hide_rejected_job_openings_api.py
pytest tests/integration/test_hide_rejected_job_openings_surfaces.py
pytest tests/ui/test_hide_rejected_job_openings_ui.py
pytest tests/unit tests/api tests/integration tests/ui
```

QA sign-off gate for this feature:
- All critical API and UI tests prove rejected jobs are absent from `/jobs`, `/jobs?bucket=rejected`, search/filter results, dashboard counts, and dashboard previews.
- `matched`, `review`, `NULL`, and unknown non-rejected jobs remain visible where expected and existing filters still work.
- Direct rejected detail route behavior is unchanged except for pre-existing source-delete visibility rules.
- Rejected job records and classification data remain persisted and unmodified by list/dashboard access.
- No blocking regression in source-delete visibility, classification transitions, dashboard rendering, or jobs filter accessibility.
- Any telemetry/count behavior either uses the filtered actionable set or clearly distinguishes visible actionable counts from total stored jobs.
