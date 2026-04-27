from __future__ import annotations

from app.domain.classification import ClassificationService
from app.domain.job_preferences import get_default_job_filter_preferences
from app.persistence.models import JobPosting, Source


def test_ambiguous_sponsorship_defaults_to_review(session):
    source = Source(name="Test", source_type="greenhouse", base_url="https://example.com", external_identifier="test", dedupe_key="x")
    session.add(source)
    session.flush()
    job = JobPosting(
        canonical_key="job-1",
        primary_source_id=source.id,
        title="Senior Python Backend Engineer",
        company_name="Example",
        job_url="https://example.com/jobs/1",
        normalized_job_url="https://example.com/jobs/1",
        location_text="Remote",
        description_text="We are hiring a Python backend engineer. Sponsorship and work authorization will be discussed during interviews.",
        sponsorship_text="Sponsorship and work authorization will be discussed during interviews.",
    )
    session.add(job)
    session.flush()

    decision = ClassificationService(session).classify_job(job, get_default_job_filter_preferences())

    assert decision.bucket == "review"
    assert decision.sponsorship_state == "ambiguous"
