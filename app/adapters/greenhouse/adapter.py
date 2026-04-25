from __future__ import annotations

from datetime import datetime

import httpx

from app.adapters.base.contracts import AdapterFetchResult, NormalizedJobCandidate
from app.domain.common import clean_text, html_to_text


class GreenhouseAdapter:
    source_type = "greenhouse"

    def validate_config(self, source: object) -> list[str]:
        errors: list[str] = []
        if not getattr(source, "external_identifier", None):
            errors.append("Greenhouse sources require external_identifier (board token).")
        return errors

    def fetch_jobs(self, source: object) -> AdapterFetchResult:
        board_token = getattr(source, "external_identifier")
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        response = httpx.get(url, timeout=20.0)
        response.raise_for_status()
        payload = response.json()
        jobs: list[NormalizedJobCandidate] = []
        for item in payload.get("jobs", []):
            jobs.append(
                NormalizedJobCandidate(
                    external_job_id=str(item.get("id")) if item.get("id") is not None else None,
                    title=clean_text(item.get("title")) or "Untitled role",
                    company_name=getattr(source, "company_name", None) or clean_text(getattr(source, "name", "")),
                    job_url=item.get("absolute_url") or getattr(source, "base_url"),
                    location_text=clean_text((item.get("location") or {}).get("name")),
                    employment_type=None,
                    remote_type=None,
                    description_text=html_to_text(item.get("content")),
                    description_html=item.get("content"),
                    sponsorship_text=html_to_text(item.get("content")),
                    posted_at=_parse_datetime(item.get("updated_at")),
                    raw_payload=item,
                )
            )
        return AdapterFetchResult(jobs=jobs)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
