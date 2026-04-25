from __future__ import annotations

from sqlalchemy import select

from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun


def seed_visibility_jobs(session):
    source = Source(
        name="Visibility Source",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/visibility",
        external_identifier="visibility",
        dedupe_key="visibility",
        is_active=True,
    )
    session.add(source)
    session.commit()
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    jobs = [
        JobPosting(canonical_key="qa-matched", primary_source_id=source.id, title="QA Matched Unique", company_name="VisibilityCo", job_url="https://example.com/matched", latest_bucket="matched", current_state="active"),
        JobPosting(canonical_key="qa-review", primary_source_id=source.id, title="QA Review Shared", company_name="VisibilityCo", job_url="https://example.com/review", latest_bucket="review", current_state="active"),
        JobPosting(canonical_key="qa-rejected", primary_source_id=source.id, title="QA Rejected Only", company_name="VisibilityCo", job_url="https://example.com/rejected", latest_bucket="rejected", current_state="active", tracking_status="saved"),
        JobPosting(canonical_key="qa-null", primary_source_id=source.id, title="QA Null Shared", company_name="VisibilityCo", job_url="https://example.com/null", latest_bucket=None, current_state="active"),
        JobPosting(canonical_key="qa-unknown", primary_source_id=source.id, title="QA Unknown Shared", company_name="VisibilityCo", job_url="https://example.com/unknown", latest_bucket="unknown", current_state="active"),
    ]
    session.add_all(jobs)
    session.flush()
    for job in jobs:
        session.add(
            JobSourceLink(
                job_posting_id=job.id,
                source_id=source.id,
                source_run_id=run.id,
                source_job_url=job.job_url,
                content_hash=f"hash-{job.canonical_key}",
                is_primary=True,
            )
        )
    session.commit()
    return source, {job.canonical_key: job.id for job in jobs}


def response_titles(response):
    return {job["title"] for job in response.json()}


def test_jobs_api_excludes_rejected_and_keeps_null_unknown_visible(client, session):
    _, job_ids = seed_visibility_jobs(session)

    response = client.get("/jobs")

    assert response.status_code == 200
    assert response_titles(response) == {"QA Matched Unique", "QA Review Shared", "QA Null Shared", "QA Unknown Shared"}
    assert session.get(JobPosting, job_ids["qa-rejected"]) is not None
    assert session.get(JobPosting, job_ids["qa-rejected"]).latest_bucket == "rejected"


def test_jobs_filters_do_not_reintroduce_rejected_jobs(client, session):
    source, _ = seed_visibility_jobs(session)

    rejected_bucket_response = client.get("/jobs?bucket=rejected")
    rejected_search_response = client.get("/jobs?search=Rejected%20Only")
    shared_search_response = client.get("/jobs?search=Shared")
    source_response = client.get(f"/jobs?source_id={source.id}")

    assert rejected_bucket_response.status_code == 200
    assert rejected_bucket_response.json() == []
    assert rejected_search_response.status_code == 200
    assert rejected_search_response.json() == []
    assert shared_search_response.status_code == 200
    assert response_titles(shared_search_response) == {"QA Review Shared", "QA Null Shared", "QA Unknown Shared"}
    assert source_response.status_code == 200
    assert "QA Rejected Only" not in response_titles(source_response)


def test_dashboard_counts_and_previews_use_actionable_jobs(client, session):
    seed_visibility_jobs(session)

    json_response = client.get("/dashboard")
    html_response = client.get("/dashboard", headers={"accept": "text/html"})

    assert json_response.status_code == 200
    assert json_response.json()["matched_count"] == 1
    assert json_response.json()["review_count"] == 1
    assert json_response.json()["rejected_count"] == 0
    assert json_response.json()["saved_needing_action"] == 0
    assert html_response.status_code == 200
    assert "QA Matched Unique" in html_response.text
    assert "QA Review Shared" in html_response.text
    assert "QA Rejected Only" not in html_response.text


def test_direct_rejected_job_detail_remains_accessible(client, session):
    _, job_ids = seed_visibility_jobs(session)

    response = client.get(f"/jobs/{job_ids['qa-rejected']}")

    assert response.status_code == 200
    assert response.json()["latest_bucket"] == "rejected"


def test_reclassification_transitions_affect_main_display_without_deleting_records(client, session):
    _, job_ids = seed_visibility_jobs(session)
    review_job = session.get(JobPosting, job_ids["qa-review"])
    rejected_job = session.get(JobPosting, job_ids["qa-rejected"])
    review_job.latest_bucket = "rejected"
    rejected_job.latest_bucket = "matched"
    session.add_all([review_job, rejected_job])
    session.commit()

    response = client.get("/jobs")
    titles = response_titles(response)

    assert response.status_code == 200
    assert "QA Review Shared" not in titles
    assert "QA Rejected Only" in titles
    assert session.scalar(select(JobPosting).where(JobPosting.id == job_ids["qa-review"])) is not None
