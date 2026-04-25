from __future__ import annotations

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.orm import aliased

from app.persistence.models import JobPosting, JobSourceLink, Source


def retained_deleted_source_job_predicate():
    return (JobPosting.latest_bucket == "matched") & (JobPosting.current_state == "active")


def associated_deleted_source_exists_predicate():
    primary_source = aliased(Source)
    linked_source = aliased(Source)
    primary_deleted = exists(
        select(primary_source.id).where(
            primary_source.id == JobPosting.primary_source_id,
            primary_source.deleted_at.is_not(None),
        )
    )
    linked_deleted = exists(
        select(JobSourceLink.id)
        .join(linked_source, linked_source.id == JobSourceLink.source_id)
        .where(
            JobSourceLink.job_posting_id == JobPosting.id,
            linked_source.deleted_at.is_not(None),
        )
    )
    return primary_deleted | linked_deleted


def visible_job_predicate():
    """Normal user-facing visibility for jobs during source-delete cleanup.

    Jobs are visible when they have no association with a deleted source, or when
    they are the one retained class from a deleted source: matched and active.
    """

    return or_(~associated_deleted_source_exists_predicate(), retained_deleted_source_job_predicate())


def apply_visible_jobs(query: Select) -> Select:
    return query.where(visible_job_predicate())


def actionable_job_status_predicate():
    """Status visibility for the main actionable jobs display.

    Only jobs explicitly classified as rejected are hidden. Jobs with NULL or
    unknown non-rejected buckets remain visible for backward compatibility and
    to preserve unclassified ingestion results.
    """

    return or_(JobPosting.latest_bucket.is_(None), JobPosting.latest_bucket != "rejected")


def main_display_job_predicate():
    """Main Jobs/Dashboard display visibility.

    Composes normal source-delete visibility with the actionable status rule.
    """

    return visible_job_predicate() & actionable_job_status_predicate()


def apply_main_display_jobs(query: Select) -> Select:
    return query.where(main_display_job_predicate())
