from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class NormalizedJobCandidate:
    external_job_id: str | None
    title: str
    company_name: str | None
    job_url: str
    location_text: str | None
    employment_type: str | None
    remote_type: str | None
    description_text: str
    description_html: str | None
    sponsorship_text: str | None
    posted_at: datetime | None
    raw_payload: dict


@dataclass
class AdapterFetchResult:
    jobs: list[NormalizedJobCandidate]
    warnings: list[str] = field(default_factory=list)


class BaseSourceAdapter(Protocol):
    source_type: str

    def validate_config(self, source: object) -> list[str]: ...

    def fetch_jobs(self, source: object) -> AdapterFetchResult: ...
