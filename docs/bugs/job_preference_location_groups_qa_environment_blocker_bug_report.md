# Bug Report

## 1. Summary

QA sign-off for the Job Preference Location grouping feature is blocked by missing Python test/runtime dependencies in the active environment and unavailable browser/a11y validation tooling. No implementation defect was confirmed by the checks that executed.

## 2. Investigation Context

- Source of report: QA execution report.
- Related feature/workflow: Frontend Revamp / UI Enhancement for `/job-preferences` Location grouped country selector.
- Branch context: `feature/job_preference_location_groups`.
- Relevant commands/workflows:
  - `python3 -m pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py`
  - `pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py`
  - Direct FastAPI/TestClient UI shell smoke.
  - Browser interaction, accessibility, responsive, and route-rendering validation from the QA plan.

## 3. Observed Symptoms

- Targeted pytest UI/static tests could not run:
  - `/opt/homebrew/opt/python@3.13/bin/python3.13: No module named pytest`
  - `zsh:1: command not found: pytest`
- Direct UI shell validation could not run:
  - `ModuleNotFoundError: No module named 'bs4'`
  - `ModuleNotFoundError: No module named 'fastapi'`
- Browser-level validation was not executed because the environment/repository did not provide an available browser automation/a11y stack.
- Expected behavior: QA environment should be able to install/use the project runtime and dev dependencies, run targeted pytest/TestClient checks, and perform the required browser/a11y/responsive validation or provide equivalent manual evidence.
- Actual behavior: static/helper checks passed, but runtime UI route rendering and browser-level acceptance criteria remained unverified.

## 4. Evidence Collected

Files inspected:

- `docs/qa/job_preference_location_groups_test_report.md`
- `docs/qa/job_preference_location_groups_test_plan.md`
- `docs/frontend/job_preference_location_groups_implementation.md`
- `docs/uiux/job_preference_location_groups_design_spec.md`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/conftest.py`
- `tests/ui/test_configurable_job_preferences_ui.py`
- `tests/ui/test_job_preference_location_groups_static.py`

Key evidence:

- QA report lines 21-29 show Python compile and JS checks passed, while pytest and FastAPI/TestClient smoke were blocked by missing modules.
- QA report lines 30-33 and 91-97 state browser interaction, accessibility, responsive, saved preference rendering, and persistence validation were not executed.
- QA report lines 35-59 include the exact blocker output: missing `pytest`, missing `bs4`, and missing `fastapi`.
- QA report lines 98-102 state `[QA SIGN-OFF BLOCKED]` with no confirmed application defect.
- `pyproject.toml` lines 11-23 declare runtime dependencies including `fastapi` and `beautifulsoup4`.
- `pyproject.toml` lines 25-29 declare the `dev` optional dependency group including `pytest` and `pytest-cov`.
- `pyproject.toml` lines 34-36 define pytest configuration with `testpaths = ["tests"]` and `addopts = "-q"`; no broken pytest command/configuration was found.
- `uv.lock` lines 339-379 include the editable project, runtime dependencies, optional `dev` dependencies, and `pytest` metadata; `uv.lock` lines 694-721 include locked `pytest` and `pytest-cov` packages.
- `README.md` lines 7-10 document setup via `pip install -e .[dev]`, and line 41 documents `pytest` as the test command.
- `tests/conftest.py` lines 5-6 imports `pytest` and `fastapi.testclient.TestClient`, matching the dependencies declared in `pyproject.toml`.
- `tests/ui/test_configurable_job_preferences_ui.py` line 3 and `tests/ui/test_job_preference_location_groups_static.py` line 5 import `BeautifulSoup` from `bs4`, matching the declared `beautifulsoup4` dependency.
- No `package.json`, `requirements*.txt`, `pytest.ini`, Playwright, or axe dependency declaration was found. Browser/a11y automation appears to be recommended by the QA plan/spec, but not implemented as an executable repository test stack.

## 5. Execution Path / Failure Trace

1. QA attempted targeted Python UI/static validation.
2. Python invoked the active interpreter at `/opt/homebrew/opt/python@3.13/bin/python3.13`.
3. The interpreter did not have the project `dev` optional dependency `pytest` installed, so `python3 -m pytest ...` failed before test collection.
4. The shell also did not have a `pytest` executable on `PATH`, so `pytest ...` failed before invoking pytest.
5. Direct TestClient smoke attempts imported test/runtime modules and failed because `beautifulsoup4`/`fastapi` were not installed in that active interpreter.
6. Browser/a11y/responsive validation could not proceed because no executable browser automation or axe tooling is present in the repository/environment.

## 6. Failure Classification

- Primary classification: Environment / Configuration Issue.
- Contributing classification: Test coverage/tooling gap for browser/a11y validation.
- Severity: Blocker.

Severity justification: QA cannot complete runtime route-rendering, interaction, accessibility, responsive, or persistence acceptance criteria. The feature has no confirmed implementation failures, but release/sign-off is blocked because required validation evidence is missing.

## 7. Root Cause Analysis

### Confirmed Root Cause

The active QA Python environment did not have the project runtime/dev dependencies installed.

- Immediate failure point: command invocation/import phase before pytest collection or TestClient route execution.
- Underlying cause: local environment setup did not install the declared project dependencies, especially `pip install -e .[dev]` or equivalent.
- Supporting evidence:
  - Missing-module errors for `pytest`, `bs4`, and `fastapi` in the QA report.
  - `pyproject.toml` declares `fastapi`, `beautifulsoup4`, and optional `dev` dependency `pytest`.
  - `README.md` documents `pip install -e .[dev]` before running `pytest`.

### Most Likely Contributing Factor

Browser interaction/a11y/responsive validation is not currently backed by an executable repository test stack.

- Supporting evidence:
  - QA plan recommends Playwright/axe/manual browser validation.
  - No `package.json` or Playwright/axe dependency declaration was found.
  - QA report states browser-level checks were not executed due unavailable tooling.

## 8. Confidence Level

High.

The missing Python dependency failures are directly explained by environment setup because the dependencies are declared in project metadata and lockfile. Confidence is lower only for the browser/a11y portion because the report does not show an attempted command; evidence supports that the repository lacks an executable browser automation stack, but manual validation could still be performed outside committed tooling.

## 9. Recommended Fix

Likely owner: release/infrastructure for environment setup; QA/test or frontend for browser/a11y test coverage if automated coverage is required.

Recommended remediation:

1. In the QA execution environment, create/activate the intended virtual environment and install the project with dev extras:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e .[dev]`
2. Re-run targeted pytest commands using the same interpreter/environment:
   - `python -m pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py`
3. For browser/a11y/responsive sign-off, choose one explicit route:
   - provide manual browser validation evidence using an available browser and screen reader; or
   - add/declare a repository-supported browser automation stack such as Playwright plus axe tooling and executable tests for the acceptance criteria.

Cautions/constraints:

- No application source change is indicated for the Python dependency blocker.
- Do not change backend/frontend implementation solely for the missing dependency errors.
- If automated browser validation is required as a release gate, dependency/test declarations will need to be added intentionally; this is test infrastructure work, not a confirmed feature implementation defect.

## 10. Suggested Validation Steps

After environment remediation:

1. Confirm `python -m pytest --version` succeeds in the active QA environment.
2. Run `python -m pytest tests/ui/test_configurable_job_preferences_ui.py tests/ui/test_job_preference_location_groups_static.py`.
3. Re-run Direct FastAPI/TestClient UI shell smoke and verify `/job-preferences` renders HTML successfully.
4. Re-run previously passing static checks to preserve regression confidence:
   - `python3 -m compileall app tests`
   - `node --check app/static/js/app.js`
   - `node --test tests/js/job_preferences_helpers.test.mjs`
5. Complete browser/manual or automated validation for region select/deselect, mixed state, hidden-selection search preservation, saved preference reload, save payload shape, keyboard operation, screen reader behavior, and responsive layouts.

## 11. Open Questions / Missing Evidence

- Which environment manager should CI/QA use as the canonical install path: pip editable install, uv sync, or another workflow?
- Is browser/a11y/responsive validation required to be automated in-repository, or is documented manual QA evidence acceptable for this release?
- If automated browser coverage is required, what framework should be standardized for the repository?
- The investigation did not execute tests per bug-investigator scope; validation after dependency installation is still required.

## 12. Final Investigator Decision

Ready for environment/test-infrastructure fix.

The Python blockers require environment setup using already declared project dependencies. Browser/a11y/responsive blockers require either manual validation capacity or explicit test-infrastructure dependency/test additions if automated evidence is mandatory.
