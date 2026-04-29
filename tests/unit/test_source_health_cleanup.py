from __future__ import annotations

from datetime import timedelta

from app.domain.source_health_cleanup import cleanup_source_health_sources
from app.persistence.models import Source, utcnow


def test_cleanup_soft_deletes_confirmed_removed_sources(session):
    invalid_lever = _source(
        name="Alkami Technology Lever",
        source_type="lever",
        external_identifier="alkami",
        company_name="Alkami Technology",
    )
    removed_greenhouse = _source(
        name="HubSpot Greenhouse",
        source_type="greenhouse",
        external_identifier="hubspot",
        company_name="HubSpot",
    )
    valid_insider = _source(
        name="Insider Lever",
        source_type="lever",
        external_identifier="insiderone",
        company_name="Insider",
    )
    session.add_all([invalid_lever, removed_greenhouse, valid_insider])
    session.commit()

    result = cleanup_source_health_sources(session)

    assert set(result.removed_source_ids) == {invalid_lever.id, removed_greenhouse.id}
    assert invalid_lever.deleted_at is not None
    assert invalid_lever.is_active is False
    assert removed_greenhouse.deleted_at is not None
    assert removed_greenhouse.is_active is False
    assert valid_insider.deleted_at is None
    assert valid_insider.is_active is True


def test_cleanup_soft_deletes_duplicates_and_keeps_recent_healthy_source(session):
    older = _source(
        name="Asana Greenhouse Old",
        source_type="greenhouse",
        external_identifier="asana",
        company_name="Asana",
        base_url="https://boards.greenhouse.io/asana",
        dedupe_key="greenhouse|old|asana",
    )
    older.health_state = "healthy"
    older.last_run_status = "success"
    older.last_run_at = utcnow() - timedelta(days=2)
    newer = _source(
        name="Asana Greenhouse New",
        source_type="greenhouse",
        external_identifier="asana",
        company_name="Asana",
        base_url="https://job-boards.greenhouse.io/asana",
        dedupe_key="greenhouse|new|asana",
    )
    newer.health_state = "healthy"
    newer.last_run_status = "success"
    newer.last_run_at = utcnow() - timedelta(hours=1)
    session.add_all([older, newer])
    session.commit()

    result = cleanup_source_health_sources(session)

    assert result.duplicate_source_ids == [older.id]
    assert older.deleted_at is not None
    assert older.is_active is False
    assert newer.deleted_at is None
    assert newer.is_active is True
    assert newer.company_provider_key == "asana|greenhouse"


def test_cleanup_is_idempotent(session):
    source = _source(name="Postman Lever", source_type="lever", external_identifier="postman", company_name="Postman")
    session.add(source)
    session.commit()

    first = cleanup_source_health_sources(session)
    second = cleanup_source_health_sources(session)

    assert first.removed_source_ids == [source.id]
    assert second.removed_source_ids == []
    assert second.duplicate_source_ids == []


def _source(
    *,
    name: str,
    source_type: str,
    external_identifier: str,
    company_name: str,
    base_url: str | None = None,
    dedupe_key: str | None = None,
) -> Source:
    return Source(
        name=name,
        source_type=source_type,
        company_name=company_name,
        base_url=base_url or f"https://example.com/{external_identifier}",
        external_identifier=external_identifier,
        config_json={},
        dedupe_key=dedupe_key or f"{source_type}|{external_identifier}",
        is_active=True,
    )
