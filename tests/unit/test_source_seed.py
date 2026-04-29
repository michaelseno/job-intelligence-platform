from __future__ import annotations

from app.domain.source_seed import VALIDATED_SOURCE_ADDITIONS, add_validated_source_additions
from app.domain.sources import build_source_company_provider_key
from app.persistence.models import Source


def test_add_validated_sources_creates_all_sources_without_notes(session):
    result = add_validated_source_additions(session)

    sources = session.query(Source).filter(Source.deleted_at.is_(None)).all()
    assert len(result.created_source_ids) == 13
    assert len(sources) == 13
    assert {source.company_name for source in sources} == {definition.company_name for definition in VALIDATED_SOURCE_ADDITIONS}
    assert all(source.notes is None for source in sources)
    assert all(source.is_active is True for source in sources)
    assert all(source.company_provider_key for source in sources)


def test_add_validated_sources_is_idempotent_and_skips_active_duplicates(session):
    first = add_validated_source_additions(session)
    second = add_validated_source_additions(session)

    sources = session.query(Source).filter(Source.deleted_at.is_(None)).all()
    assert len(first.created_source_ids) == 13
    assert second.created_source_ids == []
    assert len(second.skipped_source_keys) == 13
    assert len(sources) == 13


def test_add_validated_sources_respects_company_provider_duplicate(session):
    duplicate_definition = VALIDATED_SOURCE_ADDITIONS[0]
    duplicate_key = build_source_company_provider_key(
        duplicate_definition.source_type,
        duplicate_definition.company_name,
        duplicate_definition.name,
        None,
    )
    session.add(
        Source(
            name="Existing Point Wild Greenhouse",
            source_type=duplicate_definition.source_type,
            company_name=duplicate_definition.company_name,
            base_url="https://job-boards.greenhouse.io/pointwild",
            external_identifier=duplicate_definition.external_identifier,
            config_json={},
            dedupe_key="existing-pointwild-greenhouse",
            company_provider_key=duplicate_key,
            is_active=True,
        )
    )
    session.commit()

    result = add_validated_source_additions(session)

    assert len(result.created_source_ids) == 12
    assert duplicate_key in result.skipped_source_keys
    assert session.query(Source).filter(Source.company_name == duplicate_definition.company_name, Source.deleted_at.is_(None)).count() == 1
