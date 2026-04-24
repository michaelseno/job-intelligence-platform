from __future__ import annotations

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.sources import SourceService
from app.schemas import SourceCreateRequest


def test_update_validation_ignores_current_source(session):
    service = SourceService(session, SourceAdapterRegistry())
    source = service.create_source(
        SourceCreateRequest(
            name="Acme",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/acme",
            external_identifier="acme",
        )
    )

    validation = service.validate(
        SourceCreateRequest(
            name="Acme Updated",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/acme",
            external_identifier="acme",
        ),
        exclude_source_id=source.id,
    )

    assert validation.valid is True


def test_deleted_source_is_excluded_from_duplicate_check_and_default_listing(session):
    service = SourceService(session, SourceAdapterRegistry())
    source = service.create_source(
        SourceCreateRequest(
            name="Legacy Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/legacy",
            external_identifier="legacy",
        )
    )

    deleted = service.delete_source(source.id)
    assert deleted is not None

    validation = service.validate(
        SourceCreateRequest(
            name="Replacement Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/legacy",
            external_identifier="legacy",
        )
    )

    assert validation.valid is True
    assert service.list_sources() == []
    assert len(service.list_sources(include_deleted=True)) == 1
