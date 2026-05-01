# Job Preference Location Groups Implementation

## Summary
Implemented the Location step as a searchable region accordion with country checkboxes, region select-all/deselect-all, selected counts, clear-all support, and mixed region checkbox states.

## Files Changed
- `app/templates/preferences/job_preferences.html`
- `app/static/js/app.js`
- `app/static/css/app.css`
- `tests/ui/test_job_preference_location_groups_static.py`
- `docs/frontend/job_preference_location_groups_implementation_plan.md`
- `docs/frontend/job_preference_location_groups_implementation_report.md`

## Key Behavior
- Country options are static frontend records with stable IDs, labels, aliases, location keywords, and one primary region.
- Required regions are present, including North America with United States, Canada, and Mexico as country rows.
- Region checkboxes select/deselect all countries in the region and expose partial selection through native `indeterminate` plus `aria-checked="mixed"`.
- Search filters by country label, ID, aliases/keywords, and region label without removing hidden selected countries.
- Clear all locations resets all country selections and disables when empty.

## Data Model Compatibility
- Saved values remain country IDs in `wizard.selected_countries`.
- Generated `location_positives` remain country-derived keywords only.
- No region IDs or `selected_regions` are persisted.
- Known legacy IDs including `spain`, `united_kingdom`, `south_korea`, `czech_republic`, and `hong_kong` are preserved.
- Unknown legacy country IDs show a non-blocking warning rather than being silently ignored in the UI.

## Validation Commands
- `python3 -m compileall app tests` — passed.
- `node --check app/static/js/app.js` — passed.
- `pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py` — not runnable: `pytest` command unavailable.
- `python3 -m pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py` — not runnable: Python environment has no `pytest` module installed.
- Static country ID sanity script — passed for required legacy/North America IDs and no duplicate IDs detected by the local check.

## Commit
- `82abd0f` — `feat: group job preference locations`
