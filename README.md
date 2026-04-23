# job-intelligence-platform

Local-first FastAPI backend for the Job Intelligence Platform MVP.

## Quick start

1. Create a virtualenv and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e .[dev]`
2. Copy `.env.example` to `.env` and adjust as needed.
3. Start PostgreSQL:
   - `docker compose up -d postgres`
4. Run migrations:
   - `alembic upgrade head`
5. Start the app:
   - `uvicorn app.main:app --reload`

## MVP backend scope implemented

- manual source creation and CSV import
- Greenhouse and Lever ingestion adapters
- normalized job persistence and deterministic classification
- deduplication and source provenance
- manual keep/save and tracking status transitions
- daily digest and reminder persistence
- source run history and health summaries

## Test

- `pytest`
