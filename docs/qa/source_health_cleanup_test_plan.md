# Test Plan

## 1. Feature Overview
Validate the backend/data-ingestion source-health cleanup bugfix on branch `bugfix/source_health_cleanup`. The fix must remove confirmed invalid external 404/zero-job configured sources, preserve Insider Lever with a parser robustness fix, enforce one active source per normalized company/provider, clean existing duplicates safely, and avoid frontend changes unless proven necessary.

## 2. Acceptance Criteria Mapping
| Acceptance criterion | Validation approach |
|---|---|
| Confirm source-health 404s are external vs app/config/code issue. | Reviewed bug evidence and cleanup implementation scope; verified tests target removal of confirmed invalid configured sources rather than adapter HTTP behavior changes. |
| Remove configured sources confirmed as external 404. | Inspect `app/domain/source_health_cleanup.py`; run cleanup unit coverage for Lever and Greenhouse removals. |
| Remove HubSpot Greenhouse from configured sources. | Inspect removed Greenhouse identifiers and cleanup unit coverage. |
| Remove HubSpot Greenhouse from configured sources. | Inspect cleanup constants and unit test coverage for `hubspot`. |
| One active source per normalized company + provider; same company with different provider allowed. | Run `tests/unit/test_sources.py` duplicate prevention tests; inspect source key generation and active unique index migration. |
| Cleanup existing duplicates by keeping most recently successful/healthy source. | Run cleanup unit test for duplicate keeper selection; inspect keeper sort logic. |
| Fix Insider Lever parser bug while keeping Insider configured. | Run Lever adapter contract tests for string and mixed `lists[].content`; inspect cleanup does not remove `insiderone`. |
| Cleanup stale/duplicate project files only if directly related. | Inspect changed files list for scope. |
| Backend/data-ingestion only unless frontend issue proven. | Inspect changed files list and template files; no frontend code/template changes in implementation. |

## 3. Test Scenarios
1. Duplicate Greenhouse source with same company/provider and different base URL is rejected.
2. Same company on Greenhouse and Lever remains allowed.
3. Deleted source with same company/provider does not block a new active source.
4. Cleanup soft-deletes confirmed invalid Lever sources and HubSpot Greenhouse.
5. Cleanup preserves Insider Lever (`insiderone`).
6. Cleanup soft-deletes duplicate active company/provider rows and keeps the healthier/more recent successful source.
7. Cleanup is idempotent when executed more than once.
8. Migration adds `company_provider_key` and active unique index.
9. Lever parser handles `lists[].content` as string and mixed list/dict content.
10. Source-management/source-health-adjacent regression suite remains stable where the environment supports execution.

## 4. Edge Cases
- Legacy rows with missing `company_provider_key` are backfilled.
- Soft-deleted rows are ignored by cleanup and duplicate validation.
- Same company with different provider is not considered duplicate.
- Lever list content may be a string, list of strings, list of dicts, or malformed/unexpected entries.
- Cleanup repeated after prior execution should not re-delete rows or produce duplicate results.

## 5. Test Types Covered
- Unit: source validation and cleanup logic.
- Adapter contract: Lever parser payload variants.
- Integration: Alembic migration column/index behavior.
- Regression: source deletion, source edit/delete, source batch, CSV import, HTML/source surfaces, Greenhouse/Lever adapter contract tests.
- Static/compile: Python compile check for app and Alembic code.

## 6. Coverage Justification
The selected tests directly exercise the changed backend components (`sources`, `source_health_cleanup`, `models`, Alembic migration, Lever adapter) and include regression checks across adjacent source-management behavior. Frontend validation is limited to file-scope inspection because no frontend issue was proven and no frontend files changed.
