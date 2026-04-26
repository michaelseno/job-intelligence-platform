from __future__ import annotations

from app.domain.classification import ClassificationService
from app.domain.job_preferences import JobFilterPreferences, get_default_job_filter_preferences
from app.persistence.models import JobPosting, Source


def _source(session):
    source = Source(name="Test", source_type="greenhouse", base_url="https://example.com", external_identifier="test", dedupe_key="test")
    session.add(source)
    session.flush()
    return source


def _job(session, source, title: str, description: str, location: str = "", sponsorship: str = ""):
    job = JobPosting(
        canonical_key=title.lower().replace(" ", "-"),
        primary_source_id=source.id,
        title=title,
        company_name="Example",
        job_url=f"https://example.com/{title.lower().replace(' ', '-')}",
        normalized_job_url=f"https://example.com/{title.lower().replace(' ', '-')}",
        location_text=location,
        description_text=description,
        sponsorship_text=sponsorship,
    )
    session.add(job)
    session.flush()
    return job


def _custom_preferences() -> JobFilterPreferences:
    return JobFilterPreferences(
        schema_version=1,
        configured_at=None,
        role_positives={"platform qa": ["platform quality engineer", "quality engineer"]},
        role_negatives=["growth marketer custom"],
        remote_positives=["work anywhere custom"],
        location_positives=["lisbon custom"],
        location_negatives=["us only custom"],
        sponsorship_supported=["custom sponsor supported"],
        sponsorship_unsupported=["custom sponsor unavailable"],
        sponsorship_ambiguous=["custom work authorization"],
    )


def test_custom_role_preferences_replace_hardcoded_terms(session):
    source = _source(session)
    job = _job(session, source, "Senior Python Backend Engineer", "Python backend engineer role. custom sponsor supported")

    decision = ClassificationService(session).classify_job(job, _custom_preferences())

    assert decision.bucket == "rejected"
    assert decision.final_score == 4  # sponsorship +6 and low-text -2; no hardcoded role fallback


def test_custom_role_family_scores_once_per_family(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Platform Quality Engineer",
        "Platform quality engineer and quality engineer role with custom sponsor supported. " * 5,
        "work anywhere custom",
        "custom sponsor supported",
    )

    decision = ClassificationService(session).classify_job(job, _custom_preferences())

    assert decision.final_score == 34
    assert decision.bucket == "matched"


def test_default_preferences_preserve_existing_behavior(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Senior Python Backend Engineer",
        "We are hiring a Python backend engineer for backend APIs. Visa sponsorship available. " * 3,
        "Remote",
        "Visa sponsorship available",
    )

    decision = ClassificationService(session).classify_job(job, get_default_job_filter_preferences())


    assert decision.bucket == "matched"
    assert decision.final_score == 34
    assert decision.sponsorship_state == "supported"
