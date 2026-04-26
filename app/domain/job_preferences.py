from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import JobPosting


SCHEMA_VERSION = 1
MAX_ROLE_FAMILIES = 25
MAX_KEYWORDS_PER_ROLE_FAMILY = 50
MAX_FLAT_LIST_ENTRIES = 100
MAX_KEYWORD_LENGTH = 100

DEFAULT_ROLE_POSITIVES = {
    "python backend": ["python backend", "backend engineer", "backend developer", "python engineer"],
    "sdet": ["sdet", "software development engineer in test"],
    "qa automation": ["qa automation", "quality assurance automation", "test automation"],
    "test infrastructure": ["test infrastructure", "testing platform", "quality platform"],
    "developer productivity": ["developer productivity", "developer experience", "engineering productivity"],
}
DEFAULT_ROLE_NEGATIVES = ["sales", "account executive", "marketing", "recruiter", "designer", "hr", "finance"]
DEFAULT_REMOTE_POSITIVES = ["remote", "work from anywhere", "distributed"]
DEFAULT_LOCATION_POSITIVES = ["spain", "barcelona", "madrid"]
DEFAULT_LOCATION_NEGATIVES = ["on-site", "onsite", "must be located in", "us only"]
DEFAULT_SPONSORSHIP_UNSUPPORTED = ["no visa sponsorship", "unable to sponsor", "must be authorized to work"]
DEFAULT_SPONSORSHIP_SUPPORTED = ["visa sponsorship available", "sponsorship available", "will sponsor"]
DEFAULT_SPONSORSHIP_AMBIGUOUS = ["visa", "work authorization", "sponsorship"]


class JobFilterPreferencesError(ValueError):
    def __init__(self, errors: dict[str, list[str]]) -> None:
        self.errors = errors
        super().__init__("Invalid job filter preferences.")


@dataclass(frozen=True)
class JobFilterPreferences:
    schema_version: int
    configured_at: str | None
    role_positives: dict[str, list[str]]
    role_negatives: list[str]
    remote_positives: list[str]
    location_positives: list[str]
    location_negatives: list[str]
    sponsorship_supported: list[str]
    sponsorship_unsupported: list[str]
    sponsorship_ambiguous: list[str]

    def model_dump(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "configured_at": self.configured_at,
            "role_positives": {family: list(keywords) for family, keywords in self.role_positives.items()},
            "role_negatives": list(self.role_negatives),
            "remote_positives": list(self.remote_positives),
            "location_positives": list(self.location_positives),
            "location_negatives": list(self.location_negatives),
            "sponsorship_supported": list(self.sponsorship_supported),
            "sponsorship_unsupported": list(self.sponsorship_unsupported),
            "sponsorship_ambiguous": list(self.sponsorship_ambiguous),
        }


def _configured_at_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_default_job_filter_preferences() -> JobFilterPreferences:
    return JobFilterPreferences(
        schema_version=SCHEMA_VERSION,
        configured_at=None,
        role_positives={family: list(keywords) for family, keywords in DEFAULT_ROLE_POSITIVES.items()},
        role_negatives=list(DEFAULT_ROLE_NEGATIVES),
        remote_positives=list(DEFAULT_REMOTE_POSITIVES),
        location_positives=list(DEFAULT_LOCATION_POSITIVES),
        location_negatives=list(DEFAULT_LOCATION_NEGATIVES),
        sponsorship_supported=list(DEFAULT_SPONSORSHIP_SUPPORTED),
        sponsorship_unsupported=list(DEFAULT_SPONSORSHIP_UNSUPPORTED),
        sponsorship_ambiguous=list(DEFAULT_SPONSORSHIP_AMBIGUOUS),
    )


def _add_error(errors: dict[str, list[str]], field: str, message: str) -> None:
    errors.setdefault(field, []).append(message)


def _normalize_keyword_list(value: Any, field: str, max_entries: int, errors: dict[str, list[str]]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        _add_error(errors, field, "Must be a list of strings.")
        return []
    if len(value) > max_entries:
        _add_error(errors, field, f"Must contain no more than {max_entries} entries.")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str):
            _add_error(errors, field, f"Entry {index + 1} must be a string.")
            continue
        trimmed = item.strip()
        if not trimmed:
            continue
        if len(trimmed) > MAX_KEYWORD_LENGTH:
            _add_error(errors, field, f"Entry {index + 1} must be {MAX_KEYWORD_LENGTH} characters or fewer.")
            continue
        key = trimmed.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(trimmed)
    return normalized


def validate_job_filter_preferences(payload: Any) -> JobFilterPreferences:
    errors: dict[str, list[str]] = {}
    if not isinstance(payload, dict):
        raise JobFilterPreferencesError({"__all__": ["Preference payload must be a JSON object."]})

    if payload.get("schema_version") != SCHEMA_VERSION:
        _add_error(errors, "schema_version", f"schema_version must be {SCHEMA_VERSION}.")

    role_positives_payload = payload.get("role_positives")
    role_positives: dict[str, list[str]] = {}
    if not isinstance(role_positives_payload, dict):
        _add_error(errors, "role_positives", "Must be an object of role family keyword lists.")
    else:
        if len(role_positives_payload) > MAX_ROLE_FAMILIES:
            _add_error(errors, "role_positives", f"Must contain no more than {MAX_ROLE_FAMILIES} role families.")
        seen_families: set[str] = set()
        for family, keywords in role_positives_payload.items():
            if not isinstance(family, str) or not family.strip():
                _add_error(errors, "role_positives", "Role family names must be non-blank strings.")
                continue
            normalized_family = family.strip()
            if len(normalized_family) > MAX_KEYWORD_LENGTH:
                _add_error(errors, "role_positives", f"Role family names must be {MAX_KEYWORD_LENGTH} characters or fewer.")
                continue
            family_key = normalized_family.casefold()
            if family_key in seen_families:
                _add_error(errors, "role_positives", f"Duplicate role family '{normalized_family}'.")
                continue
            seen_families.add(family_key)
            normalized_keywords = _normalize_keyword_list(keywords, f"role_positives.{normalized_family}", MAX_KEYWORDS_PER_ROLE_FAMILY, errors)
            role_positives[normalized_family] = normalized_keywords

    preferences = JobFilterPreferences(
        schema_version=SCHEMA_VERSION,
        configured_at=payload.get("configured_at") if isinstance(payload.get("configured_at"), str) else _configured_at_now(),
        role_positives=role_positives,
        role_negatives=_normalize_keyword_list(payload.get("role_negatives"), "role_negatives", MAX_FLAT_LIST_ENTRIES, errors),
        remote_positives=_normalize_keyword_list(payload.get("remote_positives"), "remote_positives", MAX_FLAT_LIST_ENTRIES, errors),
        location_positives=_normalize_keyword_list(payload.get("location_positives"), "location_positives", MAX_FLAT_LIST_ENTRIES, errors),
        location_negatives=_normalize_keyword_list(payload.get("location_negatives"), "location_negatives", MAX_FLAT_LIST_ENTRIES, errors),
        sponsorship_supported=_normalize_keyword_list(payload.get("sponsorship_supported"), "sponsorship_supported", MAX_FLAT_LIST_ENTRIES, errors),
        sponsorship_unsupported=_normalize_keyword_list(payload.get("sponsorship_unsupported"), "sponsorship_unsupported", MAX_FLAT_LIST_ENTRIES, errors),
        sponsorship_ambiguous=_normalize_keyword_list(payload.get("sponsorship_ambiguous"), "sponsorship_ambiguous", MAX_FLAT_LIST_ENTRIES, errors),
    )

    has_positive_signal = any(preferences.role_positives.values()) or bool(preferences.remote_positives) or bool(preferences.location_positives)
    if not has_positive_signal:
        _add_error(errors, "__all__", "At least one positive matching signal is required.")

    if errors:
        raise JobFilterPreferencesError(errors)
    return preferences


def reclassify_active_jobs(session: Session, preferences: JobFilterPreferences) -> int:
    from app.domain.classification import ClassificationService

    jobs = list(session.scalars(select(JobPosting).where(JobPosting.current_state == "active")))
    classifier = ClassificationService(session)
    for job in jobs:
        classifier.classify_job(job, preferences)
    session.flush()
    return len(jobs)
