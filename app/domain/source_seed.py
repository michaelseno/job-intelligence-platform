from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.common import clean_text
from app.domain.sources import build_source_company_provider_key, build_source_dedupe_key
from app.persistence.models import Source


@dataclass(frozen=True)
class ValidatedSourceDefinition:
    company_name: str
    source_type: str
    base_url: str
    external_identifier: str

    @property
    def name(self) -> str:
        return f"{self.company_name} {self.source_type.title()}"


@dataclass(frozen=True)
class SourceSeedResult:
    created_source_ids: list[int]
    skipped_source_keys: list[str]


VALIDATED_SOURCE_ADDITIONS: tuple[ValidatedSourceDefinition, ...] = (
    ValidatedSourceDefinition("Point Wild", "greenhouse", "https://boards.greenhouse.io/pointwild", "pointwild"),
    ValidatedSourceDefinition("Fundraise Up", "greenhouse", "https://boards.greenhouse.io/fundraiseup", "fundraiseup"),
    ValidatedSourceDefinition("Shift Technology", "greenhouse", "https://boards.greenhouse.io/shifttechnology", "shifttechnology"),
    ValidatedSourceDefinition("The Economist Group", "greenhouse", "https://boards.greenhouse.io/theeconomistgroup", "theeconomistgroup"),
    ValidatedSourceDefinition("Tailscale", "greenhouse", "https://boards.greenhouse.io/tailscale", "tailscale"),
    ValidatedSourceDefinition("HighLevel", "lever", "https://jobs.lever.co/gohighlevel", "gohighlevel"),
    ValidatedSourceDefinition("Cloaked", "lever", "https://jobs.lever.co/cloaked-app", "cloaked-app"),
    ValidatedSourceDefinition("Drivetrain", "lever", "https://jobs.lever.co/drivetrain", "drivetrain"),
    ValidatedSourceDefinition("Celara", "lever", "https://jobs.lever.co/celaralabs", "celaralabs"),
    ValidatedSourceDefinition("Fullscript", "lever", "https://jobs.lever.co/fullscript", "fullscript"),
    ValidatedSourceDefinition("Panopto", "lever", "https://jobs.lever.co/panopto", "panopto"),
    ValidatedSourceDefinition("dLocal", "lever", "https://jobs.lever.co/dlocal", "dlocal"),
    ValidatedSourceDefinition("Coderio", "lever", "https://jobs.lever.co/coderio", "coderio"),
)


def add_validated_source_additions(session: Session) -> SourceSeedResult:
    created_ids: list[int] = []
    skipped_keys: list[str] = []

    for definition in VALIDATED_SOURCE_ADDITIONS:
        dedupe_key = build_source_dedupe_key(
            definition.source_type,
            definition.base_url,
            definition.external_identifier,
            None,
        )
        company_provider_key = build_source_company_provider_key(
            definition.source_type,
            definition.company_name,
            definition.name,
            None,
        )
        existing = session.scalar(
            select(Source).where(
                Source.deleted_at.is_(None),
                or_(Source.company_provider_key == company_provider_key, Source.dedupe_key == dedupe_key),
            )
        )
        if existing is not None:
            skipped_keys.append(company_provider_key)
            continue

        source = Source(
            name=definition.name,
            source_type=definition.source_type,
            adapter_key=None,
            company_name=definition.company_name,
            base_url=definition.base_url,
            external_identifier=definition.external_identifier,
            config_json={},
            notes=None,
            dedupe_key=dedupe_key,
            company_provider_key=company_provider_key,
            is_active=True,
        )
        session.add(source)
        session.flush()
        created_ids.append(source.id)

    session.commit()
    return SourceSeedResult(created_source_ids=created_ids, skipped_source_keys=skipped_keys)


def validated_source_lookup() -> dict[str, ValidatedSourceDefinition]:
    return {clean_text(source.company_name).lower(): source for source in VALIDATED_SOURCE_ADDITIONS}
