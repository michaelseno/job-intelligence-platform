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


def _visa_neutral_preferences() -> JobFilterPreferences:
    preferences = get_default_job_filter_preferences()
    return JobFilterPreferences(
        schema_version=preferences.schema_version,
        configured_at=preferences.configured_at,
        role_positives=preferences.role_positives,
        role_negatives=preferences.role_negatives,
        remote_positives=preferences.remote_positives,
        location_positives=preferences.location_positives,
        location_negatives=preferences.location_negatives,
        sponsorship_supported=[],
        sponsorship_unsupported=[],
        sponsorship_ambiguous=[],
    )


def _positive_role_description(sponsorship_text: str) -> str:
    return f"Python backend engineer role building backend APIs for a distributed platform. {sponsorship_text} " * 3


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


def test_visa_neutral_unsupported_text_does_not_reject_or_force_review(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Neutral Unsupported Python Backend Engineer",
        _positive_role_description("We are unable to sponsor visas for this role."),
        "Remote",
        "Unable to sponsor visas.",
    )

    decision = ClassificationService(session).classify_job(job, _visa_neutral_preferences())

    assert decision.bucket == "matched"
    assert decision.final_score == 28
    assert decision.sponsorship_state == "neutral"


def test_visa_neutral_supported_text_does_not_boost_score(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Neutral Supported Python Backend Engineer",
        _positive_role_description("Visa sponsorship available."),
        "Remote",
        "Visa sponsorship available.",
    )

    decision = ClassificationService(session).classify_job(job, _visa_neutral_preferences())

    assert decision.bucket == "matched"
    assert decision.final_score == 28
    assert decision.sponsorship_state == "neutral"


def test_visa_neutral_ambiguous_text_does_not_force_review(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Neutral Ambiguous Python Backend Engineer",
        _positive_role_description("Sponsorship and work authorization can be discussed."),
        "Remote",
        "Sponsorship and work authorization can be discussed.",
    )

    decision = ClassificationService(session).classify_job(job, _visa_neutral_preferences())

    assert decision.bucket == "matched"
    assert decision.final_score == 28
    assert decision.sponsorship_state == "neutral"


def test_default_preferences_reject_unsupported_sponsorship_for_positive_role(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Unsupported Python Backend Engineer",
        _positive_role_description("We are unable to sponsor visas for this role."),
        "Remote",
        "Unable to sponsor visas.",
    )

    decision = ClassificationService(session).classify_job(job, get_default_job_filter_preferences())

    assert decision.bucket == "rejected"
    assert decision.final_score == 8
    assert decision.sponsorship_state == "unsupported"


def test_default_preferences_review_ambiguous_sponsorship_for_positive_role(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "Ambiguous Python Backend Engineer",
        _positive_role_description("Sponsorship and work authorization can be discussed."),
        "Remote",
        "Sponsorship and work authorization can be discussed.",
    )

    decision = ClassificationService(session).classify_job(job, get_default_job_filter_preferences())

    assert decision.bucket == "review"
    assert decision.final_score == 28
    assert decision.sponsorship_state == "ambiguous"


def test_default_preferences_review_missing_sponsorship_for_positive_role(session):
    source = _source(session)
    job = _job(
        session,
        source,
        "No Permit Text Python Backend Engineer",
        "Python backend engineer role building backend APIs for a distributed platform. The posting describes backend API ownership. " * 3,
        "Remote",
        "",
    )

    decision = ClassificationService(session).classify_job(job, get_default_job_filter_preferences())

    assert decision.bucket == "review"
    assert decision.final_score == 28
    assert decision.sponsorship_state == "missing"
