from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry, UnsupportedAdapterError
from app.domain.common import clean_text, normalize_url, slugify
from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun, utcnow
from app.schemas import SourceCreateRequest, SourceImportResponse, SourceImportRowResult, SourceUpdateRequest


VALID_SOURCE_TYPES = {"greenhouse", "lever", "common_pattern", "custom_adapter"}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    dedupe_key: str | None = None


@dataclass
class DeleteImpactSummary:
    run_count: int
    linked_job_count: int
    tracked_job_count: int
    has_run_history: bool
    has_linked_jobs: bool


class SourceService:
    def __init__(self, session: Session, registry: SourceAdapterRegistry) -> None:
        self.session = session
        self.registry = registry

    def list_sources(self, include_deleted: bool = False) -> list[Source]:
        query = select(Source)
        if not include_deleted:
            query = query.where(Source.deleted_at.is_(None))
        return list(self.session.scalars(query.order_by(Source.created_at.desc())))

    def get_source(self, source_id: int, include_deleted: bool = False) -> Source | None:
        source = self.session.get(Source, source_id)
        if source is None:
            return None
        if not include_deleted and source.deleted_at is not None:
            return None
        return source

    def validate(self, payload: SourceCreateRequest, exclude_source_id: int | None = None) -> ValidationResult:
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
        duplicate_query = select(Source).where(Source.dedupe_key == dedupe_key, Source.deleted_at.is_(None))
        if exclude_source_id is not None:
            duplicate_query = duplicate_query.where(Source.id != exclude_source_id)
        duplicate = self.session.scalar(duplicate_query)
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
            notes=clean_text(payload.notes) or None,
            dedupe_key=validation.dedupe_key or "",
            is_active=payload.is_active,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def build_update_payload(self, source: Source, patch: SourceUpdateRequest) -> SourceCreateRequest:
        changes = patch.model_dump(exclude_unset=True)
        return SourceCreateRequest(
            name=changes.get("name", source.name),
            source_type=changes.get("source_type", source.source_type),
            base_url=changes.get("base_url", source.base_url),
            external_identifier=changes.get("external_identifier", source.external_identifier),
            adapter_key=changes.get("adapter_key", source.adapter_key),
            company_name=changes.get("company_name", source.company_name),
            is_active=changes.get("is_active", source.is_active),
            notes=changes.get("notes", source.notes),
            config_json=source.config_json,
        )

    def update_source(self, source_id: int, patch: SourceUpdateRequest) -> tuple[Source | None, ValidationResult | None]:
        source = self.get_source(source_id)
        if source is None:
            return None, None
        payload = self.build_update_payload(source, patch)
        validation = self.validate(payload, exclude_source_id=source_id)
        if not validation.valid:
            return None, validation
        source.name = clean_text(payload.name)
        source.source_type = payload.source_type
        source.adapter_key = clean_text(payload.adapter_key) or None
        source.company_name = clean_text(payload.company_name) or None
        source.base_url = clean_text(payload.base_url)
        source.external_identifier = clean_text(payload.external_identifier) or None
        source.notes = clean_text(payload.notes) or None
        source.dedupe_key = validation.dedupe_key or ""
        source.is_active = payload.is_active
        source.config_json = payload.config_json or source.config_json or {}
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source, validation

    def get_delete_impact(self, source_id: int) -> DeleteImpactSummary | None:
        source = self.get_source(source_id)
        if source is None:
            return None
        run_count = self.session.scalar(select(func.count(SourceRun.id)).where(SourceRun.source_id == source_id)) or 0
        linked_job_count = self.session.scalar(
            select(func.count(distinct(JobSourceLink.job_posting_id))).where(JobSourceLink.source_id == source_id)
        ) or 0
        tracked_job_count = self.session.scalar(
            select(func.count(distinct(JobSourceLink.job_posting_id)))
            .select_from(JobSourceLink)
            .join(JobPosting, JobPosting.id == JobSourceLink.job_posting_id)
            .where(JobSourceLink.source_id == source_id, JobPosting.tracking_status.is_not(None))
        ) or 0
        return DeleteImpactSummary(
            run_count=run_count,
            linked_job_count=linked_job_count,
            tracked_job_count=tracked_job_count,
            has_run_history=run_count > 0,
            has_linked_jobs=linked_job_count > 0,
        )

    def delete_source(self, source_id: int) -> Source | None:
        source = self.get_source(source_id)
        if source is None:
            return None
        source.deleted_at = utcnow()
        source.is_active = False
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_runnable_source(self, source_id: int) -> Source | None:
        source = self.get_source(source_id)
        if source is None:
            return None
        if not source.is_active:
            raise ValueError("Source is inactive and cannot be run.")
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
