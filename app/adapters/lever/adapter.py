from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.adapters.base.contracts import AdapterFetchResult, NormalizedJobCandidate
from app.domain.common import clean_text


class LeverAdapter:
    source_type = "lever"

    def validate_config(self, source: object) -> list[str]:
        errors: list[str] = []
        if not getattr(source, "external_identifier", None):
            errors.append("Lever sources require external_identifier (company slug).")
        return errors

    def fetch_jobs(self, source: object) -> AdapterFetchResult:
        company_slug = getattr(source, "external_identifier")
        url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
        response = httpx.get(url, timeout=20.0)
        response.raise_for_status()
        payload = response.json()
        jobs: list[NormalizedJobCandidate] = []
        for item in payload:
            description_parts = [
                item.get("descriptionPlain"),
                item.get("lists") and " ".join(entry.get("text", "") for group in item.get("lists", []) for entry in group.get("content", [])),
                item.get("additionalPlain"),
            ]
            description_text = clean_text(" ".join(part for part in description_parts if part))
            jobs.append(
                NormalizedJobCandidate(
                    external_job_id=str(item.get("id")) if item.get("id") is not None else None,
                    title=clean_text(item.get("text")) or "Untitled role",
                    company_name=getattr(source, "company_name", None) or clean_text(getattr(source, "name", "")),
                    job_url=item.get("hostedUrl") or getattr(source, "base_url"),
                    location_text=clean_text((item.get("categories") or {}).get("location")),
                    employment_type=clean_text((item.get("categories") or {}).get("commitment")),
                    remote_type=None,
                    description_text=description_text,
                    description_html=item.get("description") or item.get("additional"),
                    sponsorship_text=description_text,
                    posted_at=_parse_millis(item.get("createdAt")),
                    raw_payload=item,
                )
            )
        return AdapterFetchResult(jobs=jobs)


def _parse_millis(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
