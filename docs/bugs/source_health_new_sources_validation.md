# Bug Report

## 1. Summary
HITL release readiness for `bugfix/source_health_cleanup` is paused again because a new requested ATS source list must be validated, added by a downstream developer, and re-QA'd before release. Investigation validated all 13 proposed source endpoints against current adapter behavior: each returns HTTP 200, parses successfully, and returns at least one job. No proposed `company + provider` duplicate was found in repository definitions or the inspected local PostgreSQL `sources` table.

## 2. Investigation Context
- Source of report: HITL release gate change request.
- Branch context: current active branch `bugfix/source_health_cleanup`; no new branch should be created.
- Related workflow: source-health cleanup / source configuration additions.
- User action requested: validate proposed Greenhouse/Lever sources before any source addition.
- Important requirement: final CSV column is validation context only and must **not** be saved as source notes/description.

## 3. Observed Symptoms
- No runtime failure was reported for these proposed sources.
- Release readiness is invalidated because new source additions require validation and QA.
- Expected behavior:
  - Add only sources whose ATS API returns HTTP 200, parses with current app adapter behavior, and returns at least one job.
  - Skip invalid, empty, parser-failing, or existing duplicate `company + provider` sources.
  - Preserve one active source per normalized `company + provider`.

## 4. Evidence Collected
- Repository search found no proposed source names/slugs in tracked `*.py`, `*.md`, `*.json`, `*.yml`, `*.yaml`, `*.csv`, `*.txt`, or `*.sql` files.
- Local PostgreSQL raw query against `sources` found `0` existing rows matching proposed company names or slugs.
- Current adapter files inspected:
  - `app/adapters/greenhouse/adapter.py` uses API URL `https://boards-api.greenhouse.io/v1/boards/{external_identifier}/jobs`.
  - `app/adapters/lever/adapter.py` uses API URL `https://api.lever.co/v0/postings/{external_identifier}?mode=json` and now includes robust `_extract_lists_text()` handling for list/string Lever content.
- Direct HTTP and adapter validation were run with source stubs using current app adapter classes. All proposed sources returned HTTP 200, parsed successfully, and returned non-zero jobs.

## 5. Execution Path / Failure Trace
Validation path used for each proposed source:
1. Construct expected ATS API URL from provider and slug.
2. Fetch direct endpoint and record HTTP status/content type/response size.
3. Instantiate the current `GreenhouseAdapter` or `LeverAdapter` with a source-like stub.
4. Call `fetch_jobs()` to validate parser behavior and normalized job candidate generation.
5. Count returned jobs.
6. Search returned title/location/description text for the provided validation-context role/note where practical.
7. Check repository and local DB for existing duplicate company/provider entries.

## 6. Failure Classification
- Primary classification: **Requirements / validation gate change**, not a product defect.
- Severity: **Blocker** for release readiness because the user explicitly requested new source additions and QA rerun before release can proceed.
- Duplicate/config risk: **Not observed** for the proposed list.

## 7. Root Cause Analysis
### Confirmed Root Cause
Release readiness is blocked by a new HITL source-addition request, not by a failing existing implementation.

Supporting evidence:
- User added 13 proposed sources after QA sign-off.
- Source-addition requirements require validation before addition.
- Prior QA sign-off did not cover these new sources.

### Parser/config findings
- No parser failures were observed for the proposed sources under current adapter behavior.
- No existing duplicate `company + provider` rows were found for the proposed sources.
- `dLocal` is endpoint/parser/job-count valid, but the provided validation-context role (`Senior Automation Engineer`) was not found in title/description search; this does not violate the stated source-validity criteria.

## 8. Confidence Level
**High.** All proposed sources were checked through direct ATS HTTP and current adapter parsing, and local/repository duplicate checks found no existing matching source configuration.

## 9. Recommended Fix
Likely owner: **dev-backend** for source data addition, then **QA** for rerun.

Developer-ready guidance:
1. Add the 13 confirmed valid sources listed below.
2. Preserve `company_name`, `source_type`, `base_url`, and `external_identifier` exactly as validated unless the source creation path normalizes provider casing.
3. Do **not** save the final validation-context role/note as `notes`, description, or source metadata.
4. Before adding, ensure the local/deployed DB has migration `20260429_0003` applied because the current source model expects `company_provider_key`.
5. Use the existing source creation/service path so `company_provider_key` and duplicate validation are applied.
6. If any source is added manually/imported via CSV and a duplicate is reported at add time, skip that row and report it rather than creating a second active source.

## 10. Suggested Validation Steps
- After addition, query active sources grouped by normalized `company + provider`; all groups should have count `1`.
- Confirm the 13 new sources appear in `/sources` and `/source-health` with blank notes unless notes are intentionally set elsewhere.
- Run targeted source service tests and adapter contract tests.
- Run a source-health UI/API smoke check after the additions.
- Optionally run one ingestion per newly added source or a batch run limited to the new sources to verify persisted `SourceRun` success/warning states.

## 11. Open Questions / Missing Evidence
- Whether dLocal should still be added even though the provided role-context string was not found. Under the stated validation criteria it is valid because the endpoint returns 200, adapter parsing succeeds, and it returns jobs.
- Exact mechanism for adding sources was not specified: API/manual form, CSV import, or data migration/maintenance script.

## 12. Final Investigator Decision
**Ready for developer source addition and QA rerun.** All proposed sources are valid by the stated source-validity criteria, with the context caveat for dLocal.

## Per-source validation table

| Proposed source | Provider | API endpoint checked | HTTP / parser result | Job count | Existing duplicate? | Role-context evidence | Decision |
|---|---|---|---|---:|---|---|---|
| Point Wild | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/pointwild/jobs` | HTTP 200; adapter parsed | 15 | No | Found titles: `QA Automation Engineer (Mobile/Android)` across remote locations | Valid: add |
| Fundraise Up | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/fundraiseup/jobs` | HTTP 200; adapter parsed | 155 | No | Found titles: `Senior QA Engineer (Automation / Fullstack)` across remote locations | Valid: add |
| Shift Technology | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/shifttechnology/jobs` | HTTP 200; adapter parsed | 33 | No | Found titles: `QA Engineer - functional testing`, `QA Engineer - ISTQB foundation certified` | Valid: add |
| The Economist Group | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/theeconomistgroup/jobs` | HTTP 200; adapter parsed | 80 | No | Found title: `Quality Engineer / SDET` | Valid: add |
| Tailscale | Greenhouse | `https://boards-api.greenhouse.io/v1/boards/tailscale/jobs` | HTTP 200; adapter parsed | 48 | No | Fully remote context found practically: 44 jobs contained remote context | Valid: add |
| HighLevel | Lever | `https://api.lever.co/v0/postings/gohighlevel?mode=json` | HTTP 200; adapter parsed | 109 | No | Found titles: `Lead Software Development Engineer in Test - CRM Core Modules`, `SDET II - Core Platform`, `Software Development Engineer in Test III ...` | Valid: add |
| Cloaked | Lever | `https://api.lever.co/v0/postings/cloaked-app?mode=json` | HTTP 200; adapter parsed | 9 | No | Found title: `Quality Assurance Automation Engineer` | Valid: add |
| Drivetrain | Lever | `https://api.lever.co/v0/postings/drivetrain?mode=json` | HTTP 200; adapter parsed | 27 | No | Found titles: `Lead - Software Development Engineer in Test (SDET) / QA Manager`, `Software Development Engineer in Test (SDET) / Senior SDET` | Valid: add |
| Celara | Lever | `https://api.lever.co/v0/postings/celaralabs?mode=json` | HTTP 200; adapter parsed | 2 | No | Found title: `QA Automation Engineer (GFW - QA - 20260310)` | Valid: add |
| Fullscript | Lever | `https://api.lever.co/v0/postings/fullscript?mode=json` | HTTP 200; adapter parsed | 29 | No | Found title: `Senior SDET (Software Development Engineer in Test)` | Valid: add |
| Panopto | Lever | `https://api.lever.co/v0/postings/panopto?mode=json` | HTTP 200; adapter parsed | 15 | No | Found title: `SDET, Elai (Contractor)` | Valid: add |
| dLocal | Lever | `https://api.lever.co/v0/postings/dlocal?mode=json` | HTTP 200; adapter parsed | 107 | No | Provided role-context `Senior Automation Engineer` not found in practical title/description search; source still returns jobs | Valid by source criteria: add, with context caveat |
| Coderio | Lever | `https://api.lever.co/v0/postings/coderio?mode=json` | HTTP 200; adapter parsed | 39 | No | Found titles: `Principal QA Automation Engineer`, `QA Engineer`; also unrelated automation titles | Valid: add |

## Recommended add list
- Point Wild Greenhouse — `pointwild`
- Fundraise Up Greenhouse — `fundraiseup`
- Shift Technology Greenhouse — `shifttechnology`
- The Economist Group Greenhouse — `theeconomistgroup`
- Tailscale Greenhouse — `tailscale`
- HighLevel Lever — `gohighlevel`
- Cloaked Lever — `cloaked-app`
- Drivetrain Lever — `drivetrain`
- Celara Lever — `celaralabs`
- Fullscript Lever — `fullscript`
- Panopto Lever — `panopto`
- dLocal Lever — `dlocal`
- Coderio Lever — `coderio`

## Recommended skip list
- None by the confirmed source-validity criteria.
- Caveat: if product requires role-context match in addition to endpoint/parser/non-empty validation, review dLocal before adding because the provided `Senior Automation Engineer` context was not found.
