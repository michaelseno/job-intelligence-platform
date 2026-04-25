# Product Specification

## 1. Feature Overview
Feature name: Hide Rejected Job Openings

Update the main job openings display so that jobs classified as outright `rejected` are excluded by default. The main display must continue to show jobs that require user review and jobs that are matched.

The feature is intended to keep the user's active opportunity review surface focused on actionable jobs only: jobs worth reviewing further and jobs already identified as matches.

## 2. Problem Statement
The main job openings display currently includes jobs that have been classified as rejected. This creates unnecessary clutter and makes the list less useful because outright rejected jobs are not actionable for the user.

This matters because the job openings display is a primary workflow surface for deciding which opportunities deserve attention. Showing rejected jobs reduces scanning efficiency, inflates visible job counts, and may cause the user to revisit jobs the system has already determined should not be pursued.

## 3. User Persona / Target User
- Primary user: a job seeker using the job intelligence platform to review newly discovered job openings.
- Usage context: the user opens the main job openings view to find jobs that are either strong matches or still need review.

## 4. User Stories
- As a job seeker, I want outright rejected jobs hidden from the main job openings display, so that I only spend time on actionable opportunities.
- As a job seeker, I want review jobs to remain visible, so that I can evaluate opportunities that still need a decision.
- As a job seeker, I want matched jobs to remain visible, so that strong opportunities stay easy to access.
- As a job seeker, I want hidden rejected jobs to remain stored unless explicitly deleted by another feature, so that filtering does not unintentionally destroy data.

## 5. Goals / Success Criteria
- The main job openings display excludes jobs whose current/latest classification status is `rejected`.
- Jobs whose current/latest classification status is `review` remain visible in the main job openings display when they otherwise match existing filters.
- Jobs whose current/latest classification status is `matched` remain visible in the main job openings display when they otherwise match existing filters.
- Rejected jobs are not deleted or reclassified solely because they are hidden from the main display.
- User-facing counts associated with the main job openings display align with the displayed results and do not include hidden rejected jobs.

## 6. Feature Scope
### In Scope
- Exclude outright rejected jobs from the main job openings display by default.
- Retain `review` jobs in the main job openings display.
- Retain `matched` jobs in the main job openings display.
- Ensure default job-opening list counts, pagination, and empty states reflect the filtered result set.
- Apply the same default exclusion consistently to the primary data source used by the main job openings display, not only through client-side visual hiding.
- Preserve existing storage records for rejected jobs unless existing architecture already uses deletion as the only supported mechanism for removing jobs from this display.

### Out of Scope
- Deleting rejected jobs from storage unless existing architecture requires otherwise.
- Changing matching, review, or rejection classification logic unless needed to support filtering by current/latest classification status.
- Adding a new rejected-jobs management page.
- Adding bulk delete, restore, archive, or export flows for rejected jobs.
- Changing source ingestion behavior.
- Changing the visual design of job cards/rows beyond any text or empty-state adjustments required by the filtered list.
- Hiding rejected jobs from every administrative, debug, audit, or historical surface unless that surface is the same main job openings display or shares its default query intentionally.

## 7. Functional Requirements
1. The system must determine each job opening's display classification using the current/latest classification status available to the main job openings display.
2. The main job openings display must include jobs with display classification `matched` when they satisfy all other existing display filters.
3. The main job openings display must include jobs with display classification `review` when they satisfy all other existing display filters.
4. The main job openings display must exclude jobs with display classification `rejected` regardless of source, title, company, location, or other existing list filters.
5. The rejected-job exclusion must be applied before pagination so that pages are filled from eligible `matched` and `review` jobs rather than showing short pages due to hidden rejected rows.
6. The rejected-job exclusion must be applied before main-list result counts are calculated so that displayed counts match the visible list.
7. The rejected-job exclusion must work with existing search, sort, and filter controls on the main job openings display.
8. If a job changes classification from `review` to `rejected`, it must no longer appear in the main job openings display after the classification change is persisted and the view is refreshed or reloaded.
9. If a job changes classification from `rejected` to `review` or `matched`, it must appear in the main job openings display when it satisfies all other filters.
10. The feature must not physically delete rejected job records unless existing architecture has no separate display-filtering mechanism and deletion is explicitly approved as an implementation necessity.
11. The feature must not alter the classification status assigned to any job.
12. Direct access to a rejected job detail page is not changed by this feature unless the existing product behavior routes detail visibility through the same main job openings display eligibility rules.

## 8. Acceptance Criteria
- AC-01: Given a job with current/latest classification `rejected`, when the user opens the main job openings display, then that job is not shown in the list.
- AC-02: Given a job with current/latest classification `review`, when the user opens the main job openings display and the job satisfies all other active filters, then that job is shown in the list.
- AC-03: Given a job with current/latest classification `matched`, when the user opens the main job openings display and the job satisfies all other active filters, then that job is shown in the list.
- AC-04: Given a result set containing both rejected and non-rejected jobs, when the main job openings display calculates total results, then the total equals only the number of eligible `review` and `matched` jobs that satisfy active filters.
- AC-05: Given pagination is enabled, when rejected jobs exist before or between eligible jobs in the underlying dataset, then the first page still contains eligible `review` and `matched` jobs up to the normal page size where enough eligible jobs exist.
- AC-06: Given the user searches by a term that matches a rejected job and no eligible jobs, when the main job openings display loads search results, then the display shows the normal empty state and does not show the rejected job.
- AC-07: Given the user filters by source, company, location, or other existing filters, when matching jobs include rejected jobs, then rejected jobs remain excluded and eligible `review`/`matched` jobs remain visible.
- AC-08: Given a visible `review` job is reclassified as `rejected`, when the classification is persisted and the main job openings display is refreshed or reloaded, then the job is absent from the list and count.
- AC-09: Given a hidden `rejected` job is reclassified as `review` or `matched`, when the classification is persisted and the main job openings display is refreshed or reloaded, then the job is visible if it satisfies all other active filters.
- AC-10: Given a rejected job is hidden from the main job openings display, when storage is inspected through normal persistence mechanisms, then the job record still exists unless another pre-existing cleanup feature has deleted it.
- AC-11: Given an empty state occurs because all jobs are rejected, when the main job openings display loads, then the UI must not imply an error; it must use the existing no-results/no-jobs empty state or equivalent copy.
- AC-12: Given analytics or telemetry exists for the main job openings display, when the display loads, then emitted list/count metrics must be based on the filtered visible set or clearly distinguish total stored jobs from visible actionable jobs.

## 9. Edge Cases
- All stored jobs are `rejected`, resulting in an empty main job openings display.
- A page of underlying data contains only rejected jobs but later pages contain eligible jobs; pagination must not show an empty page if eligible jobs exist for that page request.
- A job has no classification status or a null/unknown classification.
- A job has multiple classification records with different statuses.
- A job's classification changes while the user is viewing the list.
- Existing filters/search terms match only rejected jobs.
- Rejected jobs exist with active tracking, reminders, saved state, or other user metadata.
- Dashboard widgets, badges, or counts share the same data source as the main job openings display.
- Direct navigation to a hidden rejected job detail URL.
- Import/ingestion creates jobs already classified as rejected.

## 10. Constraints
- Technical constraints:
  - Filtering must use the canonical current/latest classification status used elsewhere in the product.
  - Filtering should be implemented in the data/query layer for the main display where feasible so counts and pagination are correct.
  - The feature must preserve rejected job records unless a separately approved architecture constraint requires deletion.
- UX constraints:
  - The default main job openings experience should remain focused on actionable jobs only.
  - Existing list controls should not expose rejected jobs accidentally through search, sort, pagination, or filters.
  - Empty states should remain understandable when all available jobs are filtered out as rejected.
- Business rules:
  - `matched` and `review` are considered actionable for the main job openings display.
  - `rejected` is considered non-actionable for the main job openings display.
  - Hiding a job from the main display is not equivalent to deleting it.

## 11. Dependencies
- Existing job openings display and its backing API/query/data source.
- Existing classification/status model for `matched`, `review`, and `rejected` jobs.
- Existing list search, sort, filtering, pagination, and count behavior.
- Any dashboard or summary components that intentionally reuse the main job openings display query.
- Existing test fixtures or seed data for matched, review, and rejected jobs.
- Analytics/telemetry framework, if currently implemented for list views or job counts.

## 12. Assumptions
- A1: `matched`, `review`, and `rejected` are existing classification states or buckets in the product.
- A2: `rejected` means the job has been outright rejected and should not be part of the user's default actionable review workflow.
- A3: `review` means the job still needs user attention or decision and should remain visible.
- A4: `matched` means the job is considered a fit and should remain visible.
- A5: The main job openings display means the primary user-facing list of job openings, not necessarily every admin/debug/reporting surface that can access job records.
- A6: Current/latest classification status is the correct source of truth when multiple classification records exist.
- A7: Jobs with no classification are not explicitly requested in this change; unless existing behavior maps them to `review`, their treatment requires clarification.

## 13. Open Questions
- OQ-01: Should jobs with missing, null, or unknown classification be shown as `review` or hidden from the main job openings display?
- OQ-02: Are there any secondary surfaces, such as dashboard previews or job counts, that product considers part of the “main job openings display” and must also exclude rejected jobs?
- OQ-03: Should users have any way to intentionally view rejected jobs in the future, or is rejected-job visibility limited to non-main/admin/debug surfaces?
- OQ-04: Should direct job-detail URLs for rejected jobs remain accessible, or should they follow the same hidden behavior as the main job openings display?
- OQ-05: If analytics currently records total job inventory, should rejected jobs be excluded from those metrics or reported separately from visible actionable jobs?

## 14. Analytics / Telemetry Considerations
- If list-view telemetry exists, track the count of visible actionable jobs after rejected jobs are excluded.
- If total stored job counts are reported, distinguish them from visible main-display counts to avoid interpreting hidden rejected jobs as missing data.
- No new analytics event is required solely for hiding rejected jobs unless the existing analytics model already tracks filter application or list composition.
- Do not log job titles, descriptions, or other sensitive job content as part of telemetry for this feature.

## 15. Risks
- Counts or pagination may become inconsistent if rejected jobs are filtered only in the UI after data retrieval.
- Existing tests or user expectations may assume rejected jobs appear in the main list for debugging or audit purposes.
- Ambiguous treatment of null/unknown classifications could either hide actionable jobs or show jobs that should be excluded.
- Shared queries may unintentionally hide rejected jobs from surfaces where historical or administrative visibility is still needed.
- If classification changes occur while a user is viewing the list, the visible state may appear stale until refresh/reload unless existing real-time update behavior handles it.
