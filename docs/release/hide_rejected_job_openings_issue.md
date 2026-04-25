# GitHub Issue

## 1. Feature Name
Hide Rejected Job Openings

## 2. Problem Summary
The main job openings display currently includes jobs classified as `rejected`, creating clutter and inflating the active review surface with non-actionable opportunities. The feature should hide explicitly rejected jobs from the primary Jobs list and dashboard actionable summaries while continuing to show `matched`, `review`, and non-rejected/null/unknown jobs according to existing visibility rules.

## 3. Linked Planning Documents
- Product Spec: `docs/product/hide_rejected_job_openings_product_spec.md`
- Technical Design: `docs/architecture/hide_rejected_job_openings_technical_design.md`
- UI/UX Spec: `docs/uiux/hide_rejected_job_openings_uiux_spec.md`
- QA Test Plan: `docs/qa/hide_rejected_job_openings_test_plan.md`

## 4. Scope Summary
- in scope
  - Exclude jobs with current/latest classification `rejected` from `/jobs` HTML and JSON/API-equivalent results by default.
  - Keep `matched`, `review`, `NULL`, and unknown non-`rejected` jobs visible when they satisfy existing filters and source visibility rules.
  - Apply filtering at the backend/query layer before counts and any current or future pagination semantics.
  - Update dashboard actionable counts/previews to exclude rejected jobs.
  - Remove or suppress the `Rejected` option from the main Jobs bucket selector.
  - Preserve direct rejected job detail behavior under existing source-delete visibility rules.
- out of scope
  - Deleting, archiving, restoring, exporting, or reclassifying rejected jobs.
  - Adding a rejected-jobs management page or “show rejected” toggle.
  - Changing ingestion or classification algorithms.
  - Hiding rejected jobs from every admin, debug, audit, reminder, tracking, or historical surface unless it intentionally uses the main display query.

## 5. Implementation Notes
- frontend expectations
  - Jobs bucket selector should expose only `All actionable` or equivalent default, `Matched`, and `Review`.
  - Jobs rows/cards and dashboard actionable previews must not render rejected jobs.
  - Empty states should use normal no-results language and must not imply an error or deletion.
  - Duplicate template paths should be checked and kept consistent where active/tested.
- backend expectations
  - Add a reusable main-display/actionable visibility helper composed with existing source-delete visibility.
  - Use `JobPosting.latest_bucket` as the current display classification source for MVP.
  - Exclude only explicit `latest_bucket == "rejected"`; include `NULL` and unknown non-rejected values for backward compatibility.
  - Apply the helper to `/jobs` query construction and dashboard actionable summaries/previews.
  - Keep `/jobs/{job_id}` and mutation routes on existing visibility behavior unless product later changes detail access rules.
- dependencies or blockers
  - Depends on existing `latest_bucket` denormalization and source-delete visibility helpers.
  - No schema migration is expected.
  - Open product question remains whether null/unknown classifications should eventually be hidden instead of shown.
  - Dashboard `rejected_count` contract may need backward-compatible handling as `0` or omission.

## 6. QA Section
- planned test coverage
  - Unit tests for composed visibility predicates, explicit rejected exclusion, null/unknown inclusion, and source-delete compatibility.
  - API/integration tests for `/jobs`, bucket filters, search, source/tracking filters, dashboard summaries/previews, direct detail behavior, and classification transitions.
  - UI/template tests for absence of rejected rows/cards/options, accessible bucket selector behavior, empty states, and responsive rendering.
  - Regression tests for source-delete, classification flow, dashboard, detail routes, notifications/reminders where applicable, and duplicate templates.
- acceptance criteria mapping
  - AC-01 through AC-03: rejected hidden; review and matched visible.
  - AC-04 through AC-07: counts, search, filters, and pagination semantics operate on eligible non-rejected jobs.
  - AC-08 through AC-09: reclassification changes are reflected after persistence and reload.
  - AC-10: rejected records remain persisted and unmodified.
  - AC-11: all-rejected datasets show normal empty states.
  - AC-12: telemetry/count behavior uses or clearly distinguishes the filtered visible set.
- key edge cases
  - All jobs rejected.
  - Search/filter matches only rejected jobs.
  - `bucket=rejected` supplied manually.
  - `NULL` or unknown non-rejected bucket values.
  - Multiple classification records where latest/current status controls visibility.
  - Rejected tracked jobs, source-deleted jobs, and direct rejected detail URLs.
  - Classification changes while the user is viewing the list.
- test types expected
  - Unit, API, integration, server-rendered HTML/UI, regression, accessibility smoke, reliability, and basic security/privacy checks.

## 7. Risks / Open Questions
- Filtering only in the UI would cause inconsistent counts and future pagination issues; backend/query-layer filtering is required.
- Product may prefer strict `matched`/`review` inclusion later, which would change current null/unknown handling.
- Dashboard clients may depend on a `rejected_count` field; implementation should preserve or intentionally revise the contract.
- Tracking/reminder surfaces may still expose rejected jobs if outside the main display; confirm whether this is acceptable.
- Duplicate template paths may drift if only one path is updated.

## 8. Definition of Done
- `/jobs` default, search, sort, source, tracking, and bucket filters exclude explicit rejected jobs and retain eligible non-rejected jobs.
- Dashboard actionable counts and previews exclude rejected jobs.
- Jobs bucket selector no longer exposes `Rejected`.
- Rejected jobs are not deleted, archived, or reclassified by list/dashboard access.
- Direct rejected job detail behavior remains unchanged under existing visibility rules.
- Tests cover planned unit, API/integration, UI, regression, and edge-case scenarios from the QA test plan.
- All documented acceptance criteria are satisfied or explicitly dispositioned.
