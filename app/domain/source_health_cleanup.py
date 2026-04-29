from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.sources import build_source_company_provider_key
from app.persistence.models import Source, utcnow


REMOVED_LEVER_IDENTIFIERS = {
    "alkami",
    "browserstack",
    "circleci",
    "keepersecurity",
    "postman",
    "snyk",
    "storable",
    "subsplash",
}
REMOVED_GREENHOUSE_IDENTIFIERS = {"notion", "plaid", "hubspot"}


@dataclass(frozen=True)
class SourceHealthCleanupResult:
    removed_source_ids: list[int]
    duplicate_source_ids: list[int]
    updated_key_source_ids: list[int]


def cleanup_source_health_sources(session: Session) -> SourceHealthCleanupResult:
    """Soft-delete known-invalid/removed sources and duplicate active company/provider sources.

    The operation is idempotent: already-deleted rows are ignored, key backfills are stable,
    and duplicate rows already soft-deleted by a previous run are not selected again.
    """

    now = utcnow()
    active_sources = list(session.scalars(select(Source).where(Source.deleted_at.is_(None))))
    updated_key_ids = _backfill_company_provider_keys(active_sources)
    removed_ids = _soft_delete_removed_sources(active_sources, now)
    duplicate_ids = _soft_delete_duplicate_sources(active_sources, now)
    session.commit()
    return SourceHealthCleanupResult(
        removed_source_ids=removed_ids,
        duplicate_source_ids=duplicate_ids,
        updated_key_source_ids=updated_key_ids,
    )


def _backfill_company_provider_keys(sources: list[Source]) -> list[int]:
    updated_ids: list[int] = []
    for source in sources:
        key = build_source_company_provider_key(
            source.source_type,
            source.company_name,
            source.name,
            source.adapter_key,
        )
        if source.company_provider_key != key:
            source.company_provider_key = key
            updated_ids.append(source.id)
    return updated_ids


def _soft_delete_removed_sources(sources: list[Source], deleted_at: datetime) -> list[int]:
    removed_ids: list[int] = []
    for source in sources:
        identifier = (source.external_identifier or "").strip().lower()
        should_remove = (source.source_type == "lever" and identifier in REMOVED_LEVER_IDENTIFIERS) or (
            source.source_type == "greenhouse" and identifier in REMOVED_GREENHOUSE_IDENTIFIERS
        )
        if should_remove:
            source.deleted_at = deleted_at
            source.is_active = False
            removed_ids.append(source.id)
    return removed_ids


def _soft_delete_duplicate_sources(sources: list[Source], deleted_at: datetime) -> list[int]:
    groups: dict[str, list[Source]] = {}
    for source in sources:
        if source.deleted_at is not None:
            continue
        key = source.company_provider_key or build_source_company_provider_key(
            source.source_type,
            source.company_name,
            source.name,
            source.adapter_key,
        )
        groups.setdefault(key, []).append(source)

    duplicate_ids: list[int] = []
    for grouped_sources in groups.values():
        if len(grouped_sources) <= 1:
            continue
        keeper = max(grouped_sources, key=_source_keeper_sort_key)
        for source in grouped_sources:
            if source.id == keeper.id:
                continue
            source.deleted_at = deleted_at
            source.is_active = False
            duplicate_ids.append(source.id)
    return duplicate_ids


def _source_keeper_sort_key(source: Source) -> tuple[int, int, datetime, int]:
    healthy_rank = 1 if source.health_state == "healthy" else 0
    success_rank = 1 if source.last_run_status == "success" else 0
    recency = source.last_run_at or source.updated_at or source.created_at or datetime.min
    return (healthy_rank, success_rank, recency, source.id)
