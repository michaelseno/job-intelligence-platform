# Bug Report

## 1. Summary

QA rejected the wizard HITL correction because Visa sponsorship `No` maps to empty sponsorship keyword lists, but backend classification still treats sponsorship as `missing` and forces otherwise positive-role jobs into `review`. Sponsorship is therefore not neutral when the user does not require visa sponsorship.

## 2. Investigation Context

- Source of report: QA rejection during same-branch HITL correction validation.
- Branch context: `feature/configurable_job_filter_preferences`.
- Related feature/workflow: `/job-preferences` wizard, Visa sponsorship step, saved browser-local preferences submitted to backend classification/reclassification.
- Failing check: QA exploratory backend classification check in `docs/qa/configurable_job_preferences_qa_report.md` section 2.5.
- Relevant user action: user answers `No` to “I require visa sponsorship”; frontend maps this to `sponsorship_supported: []`, `sponsorship_unsupported: []`, and `sponsorship_ambiguous: []` before backend classification.

## 3. Observed Symptoms

- Failing workflow: backend classification with wizard-derived Visa = `No` preferences.
- Exact QA output:

```text
{'bucket': 'review', 'score': 28, 'sponsorship_state': 'missing', 'summary': 'Review because sponsorship is unclear or missing despite role alignment.'}
```

- Observed behavior:
  - Positive-role/location job is classified as `review` solely because `sponsorship_state == "missing"`.
  - The job includes explicit unsupported sponsorship text (`unable to sponsor`), but the submitted sponsorship keyword lists are empty because Visa = `No` should make sponsorship neutral.
- Expected behavior:
  - Per Product AC-11 / FR-7 / FR-12, Visa = `No` must make sponsorship neutral: sponsorship text must not increase score, decrease score, reject, or force review solely because of sponsorship signals.
  - Otherwise eligible positive-role jobs should be able to reach their normal bucket without sponsorship gating when sponsorship is disabled.

## 4. Evidence Collected

Files inspected:

- `docs/qa/configurable_job_preferences_qa_report.md`
  - Lines 21-24 identify the QA blocker.
  - Lines 137-190 provide the deterministic exploratory classification check and failing output.
  - Lines 271-278 list required corrections and regression coverage.
- `docs/product/configurable_job_preferences_product_spec.md`
  - FR-7 lines 181-191: Visa = `No` means sponsorship should be neutral.
  - FR-12 lines 253-257: sponsorship is active only when the user answers Yes and neutral when the user answers No.
  - AC-11 lines 332-336: sponsorship text must not increase score, decrease score, reject, or force review when Visa = `No`.
- `docs/architecture/configurable_job_preferences_architecture.md`
  - Lines 564-570 define current mapping: `requires_visa_sponsorship=false` maps all sponsorship keyword lists to empty arrays.
  - Lines 412-415 and 469-472 assume empty sponsorship lists represent neutral sponsorship behavior.
- `app/static/js/app.js` and `app/web/static/app.js`
  - `mapWizardToPreferences` maps `requires_visa_sponsorship ? DEFAULT_SPONSORSHIP_* : []` for all sponsorship fields.
- `tests/js/job_preferences_helpers.test.mjs`
  - Lines 144-159 verify frontend helper behavior only: Visa = `No` produces empty sponsorship lists.
  - This does not validate backend bucket behavior.
- `app/domain/job_preferences.py`
  - `JobFilterPreferences` has only three sponsorship keyword-list fields: `sponsorship_supported`, `sponsorship_unsupported`, `sponsorship_ambiguous`.
  - Validation accepts empty sponsorship lists as long as some positive role/remote/location signal exists (`has_positive_signal` lines 165-167).
- `app/domain/classification.py`
  - Line 107 initializes `sponsorship_state = "missing"` unconditionally.
  - Lines 108-121 only change state when a configured sponsorship keyword matches.
  - Lines 133-135 route any positive-role job with `sponsorship_state in {"ambiguous", "missing"}` to `review`.
  - Lines 136-138 reject positive-role jobs with `sponsorship_state == "unsupported"`.
- `tests/unit/test_classification.py` and `tests/unit/test_classification_preferences.py`
  - Existing tests cover default sponsorship behavior and custom preference replacement.
  - No Python regression test proves Visa = `No` is sponsorship-neutral in backend classification.

## 5. Execution Path / Failure Trace

1. User completes `/job-preferences` wizard and answers Visa sponsorship = `No`.
2. Frontend `mapWizardToPreferences` submits a backend DTO with all sponsorship keyword lists empty.
3. Backend validates the DTO successfully because role/location/work-arrangement positives still satisfy the positive-signal requirement.
4. `ClassificationService.classify_job()` starts with `sponsorship_state = "missing"` regardless of whether sponsorship criteria are enabled.
5. Because the sponsorship lists are empty, `supported_match`, `unsupported_match`, and `ambiguous_match` are all absent, so `sponsorship_state` remains `"missing"`.
6. The job matches a positive role, so the bucket rule `sponsorship_state in {"ambiguous", "missing"} and positive_role` fires before the normal matched threshold rule.
7. The classifier returns `bucket='review'` with a missing-sponsorship summary, violating neutral Visa = `No` requirements.

## 6. Failure Classification

- Primary classification: Application Bug.
- Severity: Blocker.
- Reproducibility: Always reproducible based on QA's deterministic exploratory check and direct code path.

Severity justification: this blocks HITL/QA acceptance of a corrected acceptance criterion and materially changes classification outcomes for users who do not require visa sponsorship.

## 7. Root Cause Analysis

### Confirmed Root Cause

- Immediate failure point: `app/domain/classification.py`, bucket selection in `ClassificationService.classify_job()` lines 133-135.
- Underlying root cause: the backend classifier treats empty sponsorship criteria as “sponsorship missing” instead of “sponsorship disabled/neutral.” The DTO currently represents Visa = `No` as empty sponsorship lists, but classification initializes `sponsorship_state` to `missing` unconditionally and applies the missing/ambiguous sponsorship review gate whenever a positive role matches.
- Supporting evidence:
  - Frontend mapping intentionally clears all sponsorship lists for Visa = `No`.
  - Product and architecture define Visa = `No` as neutral.
  - `ClassificationService` has no neutral/disabled sponsorship mode and always evaluates the missing-state review gate for positive-role jobs.

Contributing factor:
- The backend contract does not explicitly encode `requires_visa_sponsorship`; it relies on empty sponsorship keyword lists to mean sponsorship-neutral, but classifier logic was not updated to honor that contract.

## 8. Confidence Level

High.

The failing output, product requirements, frontend mapping, DTO shape, and classifier branch order all point to the same deterministic cause. No environment, data, dependency, or timing signal is involved.

## 9. Recommended Fix

- Likely owner: backend, with full-stack coordination for contract consistency.
- Likely files/modules:
  - `app/domain/classification.py` — `ClassificationService.classify_job()` sponsorship-state and bucket logic.
  - `app/domain/job_preferences.py` — only if the team chooses to make the sponsorship mode explicit in the DTO/validation contract.
  - Tests in `tests/unit/test_classification_preferences.py`, `tests/unit/test_classification.py`, and possibly `tests/api/test_configurable_job_preferences_api.py`.

Recommended contract/logic correction:

1. Define backend sponsorship-neutral mode. Minimal compatible contract: when all three sponsorship keyword lists are empty, sponsorship is disabled/neutral.
2. In `ClassificationService.classify_job()`, derive a flag similar to `sponsorship_enabled = bool(preferences.sponsorship_supported or preferences.sponsorship_unsupported or preferences.sponsorship_ambiguous)`.
3. If `sponsorship_enabled` is false:
   - do not search sponsorship text;
   - do not add sponsorship score deltas;
   - do not set `sponsorship_state` to `missing` in a way that triggers review;
   - do not apply the missing/ambiguous/unsupported sponsorship bucket gates;
   - use a neutral persisted state such as `neutral` or `not_required` if compatible with downstream display expectations.
4. If `sponsorship_enabled` is true, preserve existing Visa = `Yes` behavior: supported adds positive signal, unsupported rejects positive-role jobs, and missing/ambiguous sponsorship can force review.

Alternative if Engineering wants a more explicit long-term contract: add a validated optional DTO field such as `requires_visa_sponsorship` or `sponsorship_required` and have the frontend submit it. This is more invasive because frontend store/extraction, API validation, and tests must be updated. The minimal fix above aligns with the current architecture assumption that empty sponsorship lists represent Visa = `No`.

## 10. Suggested Validation Steps

Add/update automated tests before QA resubmission:

- Unit classification tests:
  - Visa = `No` / all sponsorship lists empty + positive role + preferred location + explicit `unable to sponsor` text does not reject or force review due to sponsorship.
  - Visa = `No` + `visa sponsorship available` text does not add sponsorship score.
  - Visa = `No` + ambiguous `visa/work authorization/sponsorship` text does not force review.
  - Visa = `Yes`/default sponsorship lists still preserve current behavior for supported, unsupported, ambiguous, and missing sponsorship cases.
- API/reclassification regression:
  - `/job-preferences/validate-and-reclassify` with wizard-derived empty sponsorship lists updates an active positive-role job without a sponsorship-driven review/reject outcome.
- Existing frontend helper tests should remain passing because they already verify empty sponsorship lists for Visa = `No`.

Commands to rerun after the backend fix:

```bash
node --check app/static/js/app.js && node --check app/web/static/app.js
node --test tests/js/job_preferences_helpers.test.mjs
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_job_preferences_validation.py tests/unit/test_classification_preferences.py tests/unit/test_classification.py tests/api/test_configurable_job_preferences_api.py tests/ui/test_configurable_job_preferences_ui.py
PYTHONPATH=. uv run --extra dev pytest
```

## 11. Open Questions / Missing Evidence

- Decide final persisted/display value for sponsorship disabled state (`neutral`, `not_required`, or another value). Current schema stores `sponsorship_state` as a string, so this appears low risk, but UI/report consumers should be checked.
- Decide whether to keep the current empty-list contract or add an explicit `requires_visa_sponsorship` field. The current architecture favors empty lists; QA noted that the absence of an explicit flag contributed to the bug.

## 12. Final Investigator Decision

Ready for developer fix.

This is a same-branch HITL blocker and a confirmed backend application bug. Route to a backend owner for classifier contract/logic correction, with full-stack review if the DTO contract is made explicit.
