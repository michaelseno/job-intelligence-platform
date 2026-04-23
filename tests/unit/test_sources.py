from __future__ import annotations

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.sources import SourceService
from app.schemas import SourceCreateRequest


def test_greenhouse_source_requires_external_identifier(session):
    service = SourceService(session, SourceAdapterRegistry())
    result = service.validate(
        SourceCreateRequest(name="GH", source_type="greenhouse", base_url="https://boards.greenhouse.io/example")
    )

    assert result.valid is False
    assert any("external_identifier" in error for error in result.errors)
