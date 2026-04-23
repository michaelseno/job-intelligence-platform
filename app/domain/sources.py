from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry, UnsupportedAdapterError
from app.domain.common import clean_text, normalize_url, slugify
from app.persistence.models import Source
from app.schemas import SourceCreateRequest, SourceImportResponse, SourceImportRowResult


VALID_SOURCE_TYPES = {"greenhouse", "lever", "common_pattern", "custom_adapter"}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    dedupe_key: str | None = None


class SourceService:
    def __init__(self, session: Session, registry: SourceAdapterRegistry) -> None:
        self.session = session
        self.registry = registry

    def list_sources(self) -> list[Source]:
        return list(self.session.scalars(select(Source).order_by(Source.created_at.desc())))

    def get_source(self, source_id: int) -> Source | None:
        return self.session.get(Source, source_id)

    def validate(self, payload: SourceCreateRequest) -> ValidationResult:
        errors: list[str] = []
        if payload.source_type not in VALID_SOURCE_TYPES:
            errors.append("Unsupported source_type.")
        if not clean_text(payload.name):
            errors.append("name is required.")
        if not clean_text(payload.base_url):
            errors.append("base_url is required.")
        if payload.source_type in {"greenhouse", "lever"} and not clean_text(payload.external_identifier):
            errors.append("external_identifier is required for greenhouse and lever sources.")
        if payload.source_type in {"common_pattern", "custom_adapter"} and not clean_text(payload.adapter_key):
            errors.append("adapter_key is required for common_pattern and custom_adapter sources.")
        dedupe_key = build_source_dedupe_key(
            payload.source_type,
            payload.base_url,
            payload.external_identifier,
            payload.adapter_key,
        )
        duplicate = self.session.scalar(select(Source).where(Source.dedupe_key == dedupe_key))
        if duplicate:
            errors.append("Duplicate source already exists.")
        if payload.source_type in VALID_SOURCE_TYPES:
            try:
                source_stub = type("SourceStub", (), payload.model_dump())()
                errors.extend(self.registry.get(payload.source_type, payload.adapter_key).validate_config(source_stub))
            except UnsupportedAdapterError as exc:
                errors.append(str(exc))
        return ValidationResult(valid=not errors, errors=errors, dedupe_key=dedupe_key)

    def create_source(self, payload: SourceCreateRequest) -> Source:
        validation = self.validate(payload)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        source = Source(
            name=clean_text(payload.name),
            source_type=payload.source_type,
            adapter_key=clean_text(payload.adapter_key) or None,
            company_name=clean_text(payload.company_name) or None,
            base_url=clean_text(payload.base_url),
            external_identifier=clean_text(payload.external_identifier) or None,
            config_json=payload.config_json or {},
            notes=payload.notes,
            dedupe_key=validation.dedupe_key or "",
            is_active=payload.is_active,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def import_csv(self, file_bytes: bytes) -> SourceImportResponse:
        reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8")))
        rows: list[SourceImportRowResult] = []
        created = skipped_duplicate = invalid = 0
        for idx, row in enumerate(reader, start=2):
            try:
                payload = SourceCreateRequest(
                    name=row.get("name", ""),
                    source_type=row.get("source_type", ""),
                    base_url=row.get("base_url", ""),
                    external_identifier=row.get("external_identifier") or None,
                    adapter_key=row.get("adapter_key") or None,
                    company_name=row.get("company_name") or None,
                    is_active=(row.get("is_active", "true").strip().lower() not in {"false", "0", "no"}),
                    notes=row.get("notes") or None,
                )
            except Exception as exc:
                invalid += 1
                rows.append(SourceImportRowResult(row_number=idx, status="invalid", message=str(exc)))
                continue
            validation = self.validate(payload)
            if not validation.valid:
                if any("Duplicate" in error for error in validation.errors):
                    skipped_duplicate += 1
                    rows.append(SourceImportRowResult(row_number=idx, status="skipped_duplicate", message="; ".join(validation.errors)))
                else:
                    invalid += 1
                    rows.append(SourceImportRowResult(row_number=idx, status="invalid", message="; ".join(validation.errors)))
                continue
            source = self.create_source(payload)
            created += 1
            rows.append(SourceImportRowResult(row_number=idx, status="created", message="source created", source_id=source.id))
        return SourceImportResponse(created=created, skipped_duplicate=skipped_duplicate, invalid=invalid, rows=rows)


def build_source_dedupe_key(source_type: str, base_url: str, external_identifier: str | None, adapter_key: str | None) -> str:
    return "|".join(
        [slugify(source_type), slugify(adapter_key), normalize_url(base_url), slugify(external_identifier)]
    )
