from __future__ import annotations

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.common import normalize_url
from app.domain.sources import SourceService
from app.persistence.models import JobPosting, JobSourceLink, SourceRun
from app.schemas import SourceCreateRequest, SourceUpdateRequest


def test_greenhouse_source_requires_external_identifier(session):
    service = SourceService(session, SourceAdapterRegistry())
    result = service.validate(
        SourceCreateRequest(name="GH", source_type="greenhouse", base_url="https://boards.greenhouse.io/example")
    )

    assert result.valid is False
    assert any("external_identifier" in error for error in result.errors)


def test_update_source_supports_partial_patch_without_self_duplicate_failure(session):
    service = SourceService(session, SourceAdapterRegistry())
    source = service.create_source(
        SourceCreateRequest(
            name="Example GH",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/example",
            external_identifier="example",
            company_name="Example",
        )
    )

    updated, validation = service.update_source(source.id, SourceUpdateRequest(notes="Updated notes"))

    assert validation is not None
    assert validation.valid is True
    assert updated is not None
    assert updated.notes == "Updated notes"
    assert updated.dedupe_key == source.dedupe_key


def test_duplicate_prevention_uses_company_provider_not_base_url(session):
    service = SourceService(session, SourceAdapterRegistry())
    service.create_source(
        SourceCreateRequest(
            name="Asana Greenhouse",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/asana",
            external_identifier="asana",
            company_name="Asana",
        )
    )

    result = service.validate(
        SourceCreateRequest(
            name="Asana GH New Host",
            source_type="greenhouse",
            base_url="https://job-boards.greenhouse.io/asana",
            external_identifier="asana",
            company_name="Asana",
        )
    )

    assert result.valid is False
    assert "Duplicate source already exists." in result.errors


def test_duplicate_prevention_allows_same_company_different_provider(session):
    service = SourceService(session, SourceAdapterRegistry())
    service.create_source(
        SourceCreateRequest(
            name="Keeper Security Greenhouse",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/keepersecurity",
            external_identifier="keepersecurity",
            company_name="Keeper Security",
        )
    )

    result = service.validate(
        SourceCreateRequest(
            name="Keeper Security Lever",
            source_type="lever",
            base_url="https://jobs.lever.co/keepersecurity",
            external_identifier="keepersecurity",
            company_name="Keeper Security",
        )
    )

    assert result.valid is True


def test_deleted_company_provider_duplicate_does_not_block_new_active_source(session):
    service = SourceService(session, SourceAdapterRegistry())
    source = service.create_source(
        SourceCreateRequest(
            name="Deleted GH",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/deleted",
            external_identifier="deleted",
            company_name="DeletedCo",
        )
    )
    service.delete_source(source.id)

    result = service.validate(
        SourceCreateRequest(
            name="Deleted GH Replacement",
            source_type="greenhouse",
            base_url="https://job-boards.greenhouse.io/deleted",
            external_identifier="deleted",
            company_name="DeletedCo",
        )
    )

    assert result.valid is True


def test_delete_impact_counts_runs_linked_jobs_and_tracked_jobs(session):
    service = SourceService(session, SourceAdapterRegistry())
    source = service.create_source(
        SourceCreateRequest(
            name="Impact Source",
            source_type="greenhouse",
            base_url="https://boards.greenhouse.io/impact",
            external_identifier="impact",
            company_name="Impact",
        )
    )
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.flush()
    job = JobPosting(
        canonical_key="impact-job",
        primary_source_id=source.id,
        title="Backend Engineer",
        company_name="Impact",
        job_url="https://example.com/jobs/impact",
        normalized_job_url=normalize_url("https://example.com/jobs/impact"),
        tracking_status="saved",
    )
    session.add(job)
    session.flush()
    session.add(
        JobSourceLink(
            job_posting_id=job.id,
            source_id=source.id,
            source_run_id=run.id,
            source_job_url=job.job_url,
            content_hash="hash",
            is_primary=True,
        )
    )
    session.commit()

    impact = service.get_delete_impact(source.id)

    assert impact is not None
    assert impact.run_count == 1
    assert impact.linked_job_count == 1
    assert impact.tracked_job_count == 1
    assert impact.has_run_history is True
    assert impact.has_linked_jobs is True
