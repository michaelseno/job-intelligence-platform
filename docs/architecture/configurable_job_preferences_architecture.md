# Technical Design

## 1. Feature Overview

This HITL correction simplifies the existing configurable Job Filter Preferences setup experience without changing the persistence boundary or the backend classification contract unless unavoidable.

The corrected `/job-preferences` experience is wizard-first:

1. Job categories from predefined multi-select options only.
2. Preferred countries from a checklist supplied by UX/Product.
3. Work arrangement multi-select with exclusive `Flexible / Any`.
4. Visa sponsorship yes/no.

The wizard selections are mapped into the already implemented underlying `JobFilterPreferences` criteria object used by backend validation, reclassification, source-run preference injection, and classification. Advanced keyword criteria remain available only after setup as collapsed/secondary settings.

Persistence remains browser `localStorage` only. Authentication, DynamoDB, backend preference storage, and cloud sync remain out of scope.

## 2. Product Requirements Summary

- First-time setup must be a guided wizard, not an implementation-level keyword form.
- Preferences remain saved only in browser `localStorage`.
- Preserve the existing backend `JobFilterPreferences` DTO/validation and classification/reclassification endpoints where possible.
- Map user-friendly wizard selections into the existing backend criteria fields used for classification.
- Job category selection is multi-select from predefined categories only; no saved custom/free-text categories.
- Country selection uses a UX/Product-approved European/Asian tech-hub checklist.
- Work arrangement supports `Remote`, `Hybrid`, `On-site`, and exclusive `Flexible / Any`.
- Visa sponsorship `Yes` means sponsorship support matters and explicit no-sponsorship signals should reject/penalize as currently supported by the underlying DTO.
- Visa sponsorship `No` means sponsorship behavior is neutral.
- Advanced lower-level keyword fields are hidden during first-time setup and collapsed after setup.

## 3. Requirement-to-Architecture Mapping

| Corrected requirement | Architecture responsibility |
| --- | --- |
| Wizard-first setup on `/job-preferences` | Replace first-time visible advanced form with a four-step wizard in the existing template/static JS. |
| Browser localStorage only | Continue storing the active payload in browser storage; do not add DB/DynamoDB persistence. |
| Preserve backend DTO where possible | Frontend maps wizard state to existing `JobFilterPreferences` before calling save/reclassify/source-run APIs. |
| Predefined categories only | Define a fixed category option catalog and reject arbitrary saved category labels in frontend validation. |
| Country checklist | Define a country option catalog with location aliases used to populate `location_positives`. |
| Flexible / Any exclusive | Frontend selection rules clear other work-arrangement selections and map to no work-arrangement restriction. |
| Visa sponsorship yes/no | Frontend mapping controls sponsorship keyword lists before backend submission. |
| Advanced hidden/collapsed | Advanced section edits the same underlying criteria object, but is not shown during first-time setup. |
| Existing classification behavior | Backend continues classifying from `JobFilterPreferences`; scoring and buckets remain unchanged. |

## 4. Technical Scope

### Current Technical Scope

- Update `/job-preferences` to render wizard-first setup when no configured preferences exist.
- Add frontend wizard state, validation, and mapping to existing `JobFilterPreferences`.
- Store both wizard selections and mapped backend criteria in one versioned localStorage envelope.
- Keep source-run preference injection and save/reclassify flow using the mapped `JobFilterPreferences` object.
- Move existing advanced keyword fields into a collapsed advanced section shown only after setup is complete.
- Add frontend tests for wizard behavior and mapping, and regression tests proving existing backend criteria payloads still work.

### Out of Scope

- Backend/cloud persistence for preferences.
- Authentication, user accounts, or DynamoDB.
- Custom/free-text saved job categories.
- New backend scoring weights or thresholds.
- New classification categories not representable by the current backend DTO.
- Replacing backend classification with frontend-only classification.

### Future Technical Considerations

- Persist the same localStorage envelope or its normalized fields to DynamoDB after auth exists.
- Store wizard selections separately from advanced criteria in a future account-backed preferences model.
- Add product-managed catalogs for countries/category aliases rather than hardcoded frontend constants.

## 5. Architecture Overview

Existing implementation context:

- Backend already exposes `JobFilterPreferences`, validation, reclassification, source-run classification, and no backend preference persistence.
- Frontend already has `/job-preferences`, `localStorage`, save/reclassify, source-run preference injection, and advanced criteria fields.

Corrected flow:

1. Browser opens `/job-preferences`.
2. If no usable active preferences exist, the page shows the wizard only.
3. Wizard selections are held as draft wizard state until Save.
4. On Save, frontend maps wizard state to `JobFilterPreferences` and posts that mapped payload to the existing validation/reclassification endpoint.
5. Backend validates and reclassifies using the existing DTO. Backend does not need to know whether the DTO came from wizard mapping or advanced editing.
6. After success, browser writes a localStorage envelope containing wizard selections and the normalized `JobFilterPreferences` returned by the backend.
7. After setup, `/job-preferences` shows saved wizard selections as the primary edit mode and exposes Advanced settings collapsed below.
8. If Advanced settings are edited and saved, the frontend submits the advanced-derived `JobFilterPreferences`, updates localStorage, and marks wizard-derived values as potentially customized where appropriate.

## 6. System Components

### Preference Wizard UI

- Existing route/template: `GET /job-preferences`, `app/web/templates/preferences/job_preferences.html`.
- First-time mode: render wizard steps only; advanced criteria are hidden.
- Post-setup mode: render wizard summary/edit controls plus collapsed Advanced settings.
- Step completion requires at least one category, at least one country, a valid work arrangement selection, and a visa sponsorship yes/no answer.

### Browser Preference Store

- Existing storage remains browser localStorage.
- Existing classification payload key may remain as implemented for compatibility, but the corrected design should store a richer envelope if feasible.
- Source-run and reclassification request injection must always submit the mapped `JobFilterPreferences`, not raw wizard state.

### Wizard-to-Criteria Mapper

- Recommended location: frontend static JS helper/module used by the preferences page and tests.
- Responsibility: deterministic mapping from wizard state to the existing backend DTO.
- Backend impact: none required if mapper outputs the existing `JobFilterPreferences` shape accepted by current validation.

### Backend Preference Validator / Classification

- Existing modules: `app/domain/job_preferences.py`, `app/domain/classification.py`, `app/domain/ingestion.py`, `app/web/routes.py`.
- Preserve existing `JobFilterPreferences` DTO and endpoints.
- Backend changes are not required for this HITL correction when the frontend submits the existing mapped `JobFilterPreferences` DTO. Backend must not receive or persist the localStorage envelope or wizard metadata in the normal save/source-run flow.

### Advanced Settings

- Same underlying fields already implemented: role positives/negatives, remote positives, location positives/negatives, sponsorship keyword groups.
- Hidden during first-time setup.
- Collapsed after setup and labeled as advanced.
- Advanced Save produces a `JobFilterPreferences` object and follows the same backend validation/reclassification/localStorage promotion flow.

## 7. Data Models

## Entity Name: JobPreferencesLocalEnvelope

### Purpose

Browser-local active preference envelope containing user-friendly wizard selections and the backend criteria payload used for classification.

### Primary Key

No backend primary key. Stored as one localStorage value.

Recommended key:

- Existing compatibility key if already implemented: `job_intelligence.job_filter_preferences.v1`.
- If introducing an envelope while preserving compatibility, keep the same key and add fields without changing the embedded backend `preferences` shape, or add `job_intelligence.job_filter_preferences.envelope.v1` and keep the old key synchronized until migration is complete.

### Fields

```json
{
  "schema_version": 1,
  "configured_at": "2026-04-27T12:00:00.000Z",
  "setup_mode": "wizard",
  "wizard": {
    "schema_version": 1,
    "selected_categories": ["python_backend", "sdet"],
    "selected_countries": ["spain", "germany"],
    "work_arrangements": ["remote", "hybrid"],
    "requires_visa_sponsorship": true
  },
  "preferences": {
    "schema_version": 1,
    "configured_at": "2026-04-27T12:00:00.000Z",
    "role_positives": {},
    "role_negatives": [],
    "remote_positives": [],
    "location_positives": [],
    "location_negatives": [],
    "sponsorship_supported": [],
    "sponsorship_unsupported": [],
    "sponsorship_ambiguous": []
  },
  "advanced_customized": false
}
```

### Ownership Model

Owned by the current browser/device context only. No account identity is added.

### Lifecycle

- Create: valid wizard Save posts mapped criteria to backend; after success, localStorage envelope is written.
- Update via wizard: regenerate simple-field-owned mapped criteria from wizard selections and save/reclassify. Wizard-owned criteria are `role_positives`, `location_positives`, `remote_positives`, and sponsorship keyword lists.
- Update via Advanced: save edited `preferences`; set `advanced_customized=true` if edited criteria diverge from wizard mapping.
- Later wizard saves overwrite the wizard-owned criteria and preserve advanced-only fields not represented by the wizard where technically possible, especially `role_negatives` and `location_negatives`.
- Delete/reset: if localStorage is cleared, setup is missing and wizard appears again.
- Migration: if an old localStorage value is a bare `JobFilterPreferences`, wrap it as `preferences` with `wizard=null` or infer wizard selections only when an exact deterministic reverse mapping is safe. If not safe, treat setup as complete and show Advanced collapsed plus a prompt to review wizard selections.

## Entity Name: WizardState

### Purpose

Captures simple user-facing setup selections before and after mapping to backend criteria.

### Fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | integer | Wizard schema, initially `1`. |
| `selected_categories` | list[string] | Option IDs from the predefined category catalog. At least one required. |
| `selected_countries` | list[string] | Country IDs from UX/Product country catalog. At least one required. |
| `work_arrangements` | list[string] | `remote`, `hybrid`, `onsite`, or exclusive `any`. At least one required. |
| `requires_visa_sponsorship` | boolean | Required yes/no answer. |

## Entity Name: JobFilterPreferences

### Purpose

Existing backend DTO used for validation, reclassification, source ingestion, and classification.

### Fields

Preserve the existing implemented DTO fields:

- `schema_version`
- `configured_at`
- `role_positives`
- `role_negatives`
- `remote_positives`
- `location_positives`
- `location_negatives`
- `sponsorship_supported`
- `sponsorship_unsupported`
- `sponsorship_ambiguous`

## 8. API Contracts

## Endpoint: GET /job-preferences

### Purpose

Render the wizard-first setup/edit page.

### Authentication / Authorization

No authentication in current scope. Browser-local ownership only.

### Request Parameters

- Optional query `next`: relative path to continue after setup.

### Request Body

None.

### Response Body

HTML. Template may include default backend criteria and wizard catalog metadata as JSON data attributes. Catalog metadata may also live entirely in frontend JavaScript; backend catalog delivery is optional and not required.

### Success Status Codes

- `200 OK`

### Error Status Codes

None expected for missing preferences.

### Validation Rules

- `next` must be same-origin relative path.

### Side Effects

None.

### Idempotency / Duplicate Handling

Safe read.

## Endpoint: POST /job-preferences/validate-and-reclassify

### Purpose

Validate a mapped `JobFilterPreferences` payload, reclassify jobs, and return normalized criteria.

### Authentication / Authorization

No authentication in current scope.

### Request Parameters

- Headers: `Content-Type: application/json`.

### Request Body

Preferred: existing backend DTO only.

```json
{
  "schema_version": 1,
  "role_positives": {},
  "role_negatives": [],
  "remote_positives": [],
  "location_positives": [],
  "location_negatives": [],
  "sponsorship_supported": [],
  "sponsorship_unsupported": [],
  "sponsorship_ambiguous": []
}
```

If implementation already accepts wrapper payloads, it may continue to accept `{ "job_preferences": { ... } }`, but backend should ignore wizard metadata for current scope.

### Response Body

```json
{
  "preferences": { "schema_version": 1 },
  "reclassification": { "jobs_reclassified": 42 }
}
```

### Success Status Codes

- `200 OK`

### Error Status Codes

- `422 Unprocessable Entity` for invalid mapped criteria.
- Existing server error behavior for unexpected reclassification failure.

### Validation Rules

Existing `JobFilterPreferences` validation remains authoritative.

### Side Effects

- Reclassifies active jobs and updates current decision outputs.
- Does not persist preferences on backend.

### Idempotency / Duplicate Handling

Outcome-idempotent but decision-row append behavior remains as implemented.

## Endpoint: POST /sources/{source_id}/run

### Purpose

Run source ingestion and classify fetched jobs using the mapped active `JobFilterPreferences` from localStorage.

### Authentication / Authorization

Existing source access behavior; no new auth.

### Request Parameters

- Existing path/form parameters.
- HTML form field `job_preferences_json`: must contain the mapped backend DTO, not raw wizard state.

### Request Body

Existing source-run body plus `job_preferences_json`, or JSON body with `job_preferences`.

### Response Body

Existing source-run response/redirect.

### Success Status Codes

Existing behavior.

### Error Status Codes

- `409 Conflict` when preferences are missing.
- `422 Unprocessable Entity` when mapped preferences are invalid.

### Validation Rules

Existing backend criteria validation.

### Side Effects

Existing ingestion and classification writes.

### Idempotency / Duplicate Handling

Existing ingestion deduplication remains unchanged.

## 9. Frontend Impact

### Components Affected

- `app/web/templates/preferences/job_preferences.html`: replace first-time always-visible advanced panels with wizard steps.
- `app/web/static/app.js` and mirrored static bundle if present: add wizard state, option catalogs, mapping, exclusive work-arrangement behavior, advanced collapsed behavior, localStorage envelope migration, and source-run injection compatibility.
- Stylesheets: add wizard/progress/step/advanced collapsed styling.
- Existing source-run forms: continue relying on JS to inject mapped `JobFilterPreferences`.

### API Integration

- Save wizard: `WizardState -> JobFilterPreferences -> POST /job-preferences/validate-and-reclassify -> write localStorage envelope`.
- Save advanced: edited advanced fields -> `JobFilterPreferences -> POST /job-preferences/validate-and-reclassify -> update localStorage envelope`.
- Source run: read envelope, extract `preferences`, inject `job_preferences_json`.

### UI States

- First-time setup: wizard only; no advanced keyword/scoring fields visible.
- Wizard step errors: missing category/country/work arrangement/sponsorship answer.
- Category search/typeahead: filters predefined options only; does not create custom categories.
- Work arrangement: selecting `Flexible / Any` clears `Remote`, `Hybrid`, and `On-site`; selecting a specific arrangement clears `Flexible / Any`.
- Post-setup: wizard summary/edit mode plus collapsed Advanced settings.
- Advanced customized: show a clear note that advanced criteria may differ from wizard defaults.
- Save/reclassifying/loading, validation error, storage unavailable, and save success states remain as previously designed.

## 10. Backend Logic

### Responsibilities

- Continue validating only `JobFilterPreferences` criteria payloads.
- Continue reclassification and source-run classification using the existing DTO.
- Do not persist wizard state or preferences server-side.

### Validation Flow

No backend validation change is required if frontend submits the existing DTO. Existing validation continues to trim, deduplicate, enforce schema version, enforce list limits, and require at least one positive signal.

### Business Rules

- Existing classification scoring and bucket rules remain unchanged.
- Wizard choices do not introduce new scoring weights; they only populate existing criteria lists.
- Sponsorship-neutral behavior for `requires_visa_sponsorship=false` is represented by empty sponsorship keyword lists in the mapped DTO.

### Persistence Flow

- No backend preference persistence.
- Decision persistence remains unchanged.

### Error Handling

- If mapped preferences fail backend validation, frontend must not update localStorage active preferences.
- If localStorage write fails after backend success, frontend must surface a blocking error and not claim setup is complete.

## 11. File Structure

Recommended implementation changes for this HITL correction:

```text
app/web/templates/preferences/job_preferences.html   # wizard-first layout; advanced collapsed after setup
app/web/static/app.js                                # wizard state, mapping, storage envelope, source-run injection
app/static/js/app.js                                 # mirrored bundle if project requires duplicate static path
app/web/static/styles.css                            # wizard/advanced styling if present
app/static/css/app.css                               # mirrored CSS if present
tests/js/job_preferences_helpers.test.mjs            # mapping and localStorage envelope tests
tests/ui/test_configurable_job_preferences_ui.py     # wizard/advanced behavior
tests/unit/test_job_preferences_validation.py        # backend DTO regression only if needed
tests/api/test_configurable_job_preferences_api.py   # existing endpoint regression
```

Backend files do not need to change for this HITL correction. Change backend files only if the current route parsing cannot accept the existing mapped DTO or if Engineering intentionally chooses server-rendered catalog metadata.

## 12. Security

- Browser localStorage remains the only preference store; do not send wizard metadata except where needed for validation/reclassification of mapped criteria.
- Backend must not trust localStorage-derived payloads; existing validation remains mandatory.
- Do not log raw wizard selections or preference keywords; log only counts/flags.
- Prevent custom category injection by validating option IDs on the frontend and, if backend receives wizard metadata in future, validate against a server-side catalog.
- Preserve relative-only `next` redirect handling.

## 13. Reliability

- Mapping must be deterministic and test-covered; same wizard state must always produce the same backend DTO.
- Source-run injection must read the latest localStorage envelope at submit time to avoid stale criteria.
- Advanced edits can make criteria diverge from wizard selections; UI must clearly communicate this and preserve the exact advanced DTO used for classification.
- Existing synchronous reclassification remains acceptable for current scope.
- If browser storage is unavailable, setup cannot complete.

## 14. Dependencies

- Existing backend `JobFilterPreferences` DTO and validation.
- Existing reclassification endpoint and source-run preference injection behavior.
- Approved initial country checklist and display copy.
- Existing localStorage guard and missing-preferences flow.

## 15. Assumptions

- The existing backend DTO can represent all wizard selections adequately.
- `Hybrid` and `On-site` are represented as positive work-arrangement text keywords in the current keyword-based model, without adding new scoring categories.
- `Flexible / Any` means no work-arrangement restriction and therefore maps to an empty `remote_positives` list unless Advanced overrides it.
- Visa sponsorship `No` means neutral sponsorship handling, represented by empty sponsorship supported/unsupported/ambiguous lists.
- Advanced settings edit the same underlying backend DTO and are not a separate rule layer.

## 16. Risks / Known Limitations

- Mapping `On-site` as a positive work-arrangement term preserves current keyword mechanics but does not create a true structured location constraint. This is an accepted limitation of the current DTO/classification model.
- Reverse-mapping old advanced-only localStorage payloads into wizard selections may be lossy; safest behavior is to keep setup complete and ask user to review wizard selections.
- Server-rendered pages still cannot directly read `localStorage`; existing client guard/marker behavior remains a known non-blocking limitation, not a release blocker.

## 17. Implementation Notes

### Key Contracts / Mapping Rules

#### LocalStorage Contract

- Active classification source for backend requests: `envelope.preferences` if envelope exists; otherwise legacy bare `JobFilterPreferences`.
- Wizard display source: `envelope.wizard` when available.
- Setup complete when valid `preferences` exists and either valid `wizard` exists or legacy advanced preferences have been accepted/migrated.

#### Category Catalog and Mapping

Use stable option IDs. Display labels may change without changing IDs. Keyword mapping is deterministic and derived from the current default role-family keyword groups in `app/domain/job_preferences.py` / `app/domain/classification.py`.

| Category ID | Display label | `role_positives` family | Keywords |
| --- | --- | --- | --- |
| `python_backend` | Python Backend | `python backend` | `python backend`, `python engineer` |
| `backend_engineer` | Backend Engineer | `backend engineer` | `backend engineer`, `backend developer` |
| `sdet` | SDET | `sdet` | `sdet`, `software development engineer in test` |
| `qa_automation` | QA Automation | `qa automation` | `qa automation`, `quality assurance automation` |
| `test_automation` | Test Automation | `test automation` | `test automation` |
| `test_infrastructure` | Test Infrastructure | `test infrastructure` | `test infrastructure`, `testing platform`, `quality platform` |
| `developer_productivity` | Developer Productivity / Developer Experience | `developer productivity` | `developer productivity`, `developer experience`, `engineering productivity` |

Selected categories are converted to a `role_positives` object containing only selected families. Predefined category IDs only; arbitrary typeahead text is never saved. Categories that originate from the same historical default family are intentionally split only where required by the HITL-approved category list; keywords must be de-duplicated case-insensitively within each generated family.

#### Country Catalog and Mapping

Each country option must have:

```json
{
  "id": "spain",
  "label": "Spain",
  "location_keywords": ["spain"]
}
```

Mapping rule: concatenate and case-insensitively deduplicate `location_keywords` for selected countries into `location_positives`.

The initial country catalog is approved. Use stable IDs and explicit keyword aliases below.

| Country ID | Display label | `location_keywords` |
| --- | --- | --- |
| `spain` | Spain | `spain` |
| `portugal` | Portugal | `portugal` |
| `germany` | Germany | `germany` |
| `netherlands` | Netherlands | `netherlands`, `holland` |
| `ireland` | Ireland | `ireland` |
| `united_kingdom` | United Kingdom | `united kingdom`, `uk`, `britain`, `great britain` |
| `france` | France | `france` |
| `switzerland` | Switzerland | `switzerland` |
| `sweden` | Sweden | `sweden` |
| `denmark` | Denmark | `denmark` |
| `finland` | Finland | `finland` |
| `poland` | Poland | `poland` |
| `estonia` | Estonia | `estonia` |
| `czech_republic` | Czech Republic | `czech republic`, `czechia` |
| `lithuania` | Lithuania | `lithuania` |
| `romania` | Romania | `romania` |
| `singapore` | Singapore | `singapore` |
| `japan` | Japan | `japan` |
| `south_korea` | South Korea | `south korea`, `korea` |
| `india` | India | `india` |
| `taiwan` | Taiwan | `taiwan` |
| `hong_kong` | Hong Kong | `hong kong`, `hk` |
| `malaysia` | Malaysia | `malaysia` |
| `thailand` | Thailand | `thailand` |
| `vietnam` | Vietnam | `vietnam` |
| `philippines` | Philippines | `philippines` |
| `indonesia` | Indonesia | `indonesia` |

#### Work Arrangement Mapping

| Wizard selection | DTO mapping |
| --- | --- |
| `remote` | Add `remote`, `work from anywhere`, `distributed` to `remote_positives`. |
| `hybrid` | Add `hybrid` to `remote_positives`. |
| `onsite` | Add `on-site`, `onsite` to `remote_positives` as positive work-arrangement text signals. |
| `any` / Flexible / Any | Exclusive. Clear specific arrangements and map to `remote_positives: []`. |

`Flexible / Any` must not add a keyword and must not act as a restriction.

#### Visa Sponsorship Mapping

| Wizard answer | DTO mapping |
| --- | --- |
| `requires_visa_sponsorship=true` | Use default sponsorship supported, unsupported, and ambiguous keyword lists. Explicit unsupported postings continue to receive the existing negative sponsorship behavior. |
| `requires_visa_sponsorship=false` | Set `sponsorship_supported: []`, `sponsorship_unsupported: []`, `sponsorship_ambiguous: []` so sponsorship is neutral. |

#### Negative Criteria Defaults

- `role_negatives`: keep the existing default negative role keyword list unless Advanced overrides it.
- `location_negatives`: for first-time wizard-derived preferences, default to an empty list to avoid contradicting selected countries or `On-site`. If an existing saved envelope already has advanced `location_negatives`, preserve them on later wizard saves because this field is not represented by the wizard.

#### Advanced Override Behavior

- First-time setup: Advanced section not rendered or hidden with no primary affordance.
- Post-setup: Advanced section collapsed by default.
- Advanced Save updates `preferences` directly and sets `advanced_customized=true`.
- Wizard Save after advanced customization regenerates and overwrites wizard-owned generated criteria: `role_positives`, `location_positives`, `remote_positives`, `sponsorship_supported`, `sponsorship_unsupported`, and `sponsorship_ambiguous`.
- Wizard Save preserves advanced-only fields not represented by the wizard where technically possible, especially `role_negatives` and `location_negatives`.
- After Wizard Save, keep `advanced_customized=true` only if preserved advanced-only fields still differ from wizard/default baselines; otherwise set it to `false`.
- Source-run and reclassification always use the current saved `preferences` object, regardless of whether it came from wizard or advanced editing.

### Backend Impact Assessment

- Required backend changes: none, assuming existing endpoints accept the current `JobFilterPreferences` DTO and frontend mapper submits that DTO.
- Optional backend changes only: expose category/country catalogs in template context if Engineering prefers server-provided metadata. Backend should not accept or persist the localStorage envelope unless an existing endpoint already returns/accepts metadata.
- Not required: new SQLAlchemy model, Alembic migration, DynamoDB integration, auth, or backend storage of wizard selections.
