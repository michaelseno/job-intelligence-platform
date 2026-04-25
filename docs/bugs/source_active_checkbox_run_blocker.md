# Source Active Checkbox Run Blocker

## Observed Behavior
- A user creates a Greenhouse source with the `Source is active` checkbox checked.
- The created source appears in the Sources inventory with an `Inactive` badge.
- Clicking/run-submitting the source sends `POST /sources/9/run?next=/sources` and receives `409 Conflict` with `{"detail":"Source is inactive and cannot be run."}`.
- The source can still show `adapter=greenhouse`, `health=Healthy`, and `last run=Never run`, but `is_active=False` blocks ingestion.

## Expected Behavior
- A checked `Source is active` checkbox should persist the source with `is_active=True`.
- Newly created active sources should render as `Active` and expose/allow the run action.
- `POST /sources/{id}/run` should not return the inactive-source `409` for a source created with the checkbox checked.

## Reproduction Steps
1. Open the Sources create form.
2. Enter:
   - `source_type`: `greenhouse`
   - `base_url`: `https://job-boards.greenhouse.io/devrev`
   - `external_identifier`: `devrev`
   - `adapter_key`: blank
   - leave/check `Source is active` as checked
3. Submit `Create source`.
4. Observe the created source row renders `Inactive`.
5. Submit/run the source.
6. Observe `409 Conflict` with `{"detail":"Source is inactive and cannot be run."}`.

## Evidence / Code References
- Active template resolution prefers `app/templates` before `app/web/templates`: `app/web/routes.py:44-47` builds `Jinja2Templates(directory=[app/templates, app/web/templates])`.
- The active create/edit templates in `app/templates` submit the checked checkbox as `is_active=true`:
  - `app/templates/sources/index.html:83`: `<input type="checkbox" name="is_active" value="true" ...> Source is active`
  - `app/templates/sources/edit.html:22`: `<input type="checkbox" name="is_active" value="true" ...> Source is active`
- Backend form parsing only treats the literal browser-default value `on` as active:
  - `app/web/routes.py:333-344`, especially `app/web/routes.py:343`: `"is_active": form.get("is_active") == "on"`
- The domain service persists the parsed payload value directly:
  - `app/domain/sources.py:86-101`, especially `is_active=payload.is_active` at line 100.
- Run blocking is based on persisted `source.is_active`:
  - `app/domain/sources.py:177-183`, especially line 182 raises `ValueError("Source is inactive and cannot be run.")`.
  - `app/web/routes.py:646-658` converts that `ValueError` into `409 Conflict`.
- Schema/model defaults are not the cause for this HTML path:
  - `app/schemas.py:8-16` defaults `SourceCreateRequest.is_active` to `True`, but `parse_source_form` explicitly passes `False` when form value is `true` instead of `on`.
  - `app/persistence/models.py:39` defaults `Source.is_active` to `True`, but `SourceService.create_source` explicitly assigns the parsed payload value.
- Existing coverage misses this exact mismatch:
  - `tests/integration/test_html_views.py:88-103` posts form data with `"is_active": "on"`, so it matches the parser but not the rendered `app/templates` checkbox value.
  - API tests use JSON booleans and do not exercise the HTML checkbox serialization path.
- There is also a newer duplicate template under `app/web/templates/sources/index.html:62` whose checkbox omits `value`, causing browsers to submit `on`; however, because `app/templates` is first in the template directory list, the `app/templates` version is the likely rendered form.

## Suspected Root Cause
Confirmed root cause: frontend/backend contract mismatch on the HTML checkbox value.

The rendered Sources create/edit form submits `is_active=true`, but `parse_source_form()` only accepts `is_active == "on"`. Therefore a checked checkbox from the active template is parsed as `False`, persisted as inactive, rendered inactive in inventory, and subsequently rejected by `get_runnable_source()` with the reported `409`.

This is not a rendering-only mismatch and not a schema/model default issue; the source is actually persisted with `is_active=False` on the HTML form path.

## Impact / Severity
- Severity: High validation blocker.
- Impact: Users cannot run newly created sources from the UI when the checked active checkbox is submitted as `true`. This blocks initial ingestion for affected sources and creates a confusing state (`Healthy` but `Inactive`/never runnable).

## Recommended Fix Owner and Fix Approach
- Owner: Backend-primary, with frontend/template coordination.
- Recommended backend fix: update `parse_source_form()` to parse standard truthy checkbox values, e.g. treat `{"on", "true", "1", "yes"}` as active and missing/false-like values as inactive.
- Recommended frontend/template cleanup: align duplicate source templates so they use a consistent checkbox value/label and avoid divergence between `app/templates` and `app/web/templates`.
- Consider verifying whether both template trees are still intended; if not, remove or de-prioritize stale templates to reduce future mismatches.

## Regression Tests to Add / Update
- Add an HTML form integration test that posts `is_active=true` to `POST /sources` and asserts the created source is active in the response/page/database.
- Update/extend `tests/integration/test_html_views.py::test_html_forms_redirect_for_source_and_tracking` to use the exact checkbox value rendered by the active template (`true`) or to fetch the form first and submit its actual input value.
- Add a test for `POST /sources/{id}/edit` with `is_active=true` to ensure active state remains/updates to active.
- Add a run validation test: create via HTML form with checked `is_active=true`, then `POST /sources/{id}/run` and assert it does not fail with the inactive-source `409`.

## Open Questions / Missing Evidence
- No browser/network capture from the user's session was available beyond the report. The code strongly indicates the submitted form value was `true`, matching the active `app/templates` form.
- Confirm at runtime which template tree is intended long term (`app/templates` vs `app/web/templates`) before deleting or consolidating templates.
