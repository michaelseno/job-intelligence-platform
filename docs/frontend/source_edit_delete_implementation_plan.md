# Implementation Plan

## 1. Feature Overview
Add server-rendered source edit and delete management flows, plus list/detail action entry points and inactive-state UX updates.

## 2. Technical Scope
- Add HTML edit and delete routes for sources
- Add edit and delete templates
- Update source list and detail templates with status and actions
- Filter deleted sources from management-facing selectors and source health views
- Support inactive run-state messaging in HTML surfaces

## 3. UI/UX Inputs
- `docs/architecture/source_edit_delete_technical_design.md`
- `docs/uiux/source_edit_delete_design_spec.md`
- Existing source create/list/detail Jinja patterns and shared button/badge styles

## 4. Files Expected to Change
- `app/web/routes.py`
- `app/domain/sources.py`
- `app/domain/operations.py`
- `app/persistence/models.py`
- `app/web/templates/sources/index.html`
- `app/web/templates/sources/detail.html`
- `app/web/templates/sources/edit.html`
- `app/web/templates/sources/delete_confirm.html`
- `app/web/static/styles.css`
- targeted source edit/delete tests

## 5. Dependencies / Constraints
- Must preserve PRG and existing server-rendered validation behavior
- Must not disturb unrelated untracked docs/files in the branch
- No commit, PR, or remote push in this task

## 6. Assumptions
- Minimal web-layer support can extend source service behavior needed by the frontend flow
- Soft-delete is represented by `deleted_at`
- Existing database migration work may be handled separately if not already present

## 7. Validation Plan
- Run targeted unit tests for source service edit/delete behavior
- Run targeted HTML integration tests for source edit/delete flows
- Run a focused pytest pass for changed source-related tests if feasible
