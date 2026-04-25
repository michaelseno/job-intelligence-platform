from __future__ import annotations

from bs4 import BeautifulSoup

from app.persistence.models import JobPosting, JobSourceLink, Source, SourceRun


def seed_ui_jobs(session):
    source = Source(
        name="UI Visibility Source",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/ui-visibility",
        external_identifier="ui-visibility",
        dedupe_key="ui-visibility",
        is_active=True,
    )
    session.add(source)
    session.commit()
    run = SourceRun(source_id=source.id, trigger_type="manual", status="success")
    session.add(run)
    session.commit()
    jobs = [
        JobPosting(
            canonical_key="ui-matched-actionable",
            primary_source_id=source.id,
            title="UI Matched Actionable",
            company_name="ActionableCo",
            job_url="https://example.com/ui-matched",
            latest_bucket="matched",
            current_state="active",
        ),
        JobPosting(
            canonical_key="ui-review-actionable",
            primary_source_id=source.id,
            title="UI Review Actionable",
            company_name="ActionableCo",
            job_url="https://example.com/ui-review",
            latest_bucket="review",
            current_state="active",
        ),
        JobPosting(
            canonical_key="ui-rejected-hidden",
            primary_source_id=source.id,
            title="UI Rejected Hidden",
            company_name="HiddenCo",
            job_url="https://example.com/ui-rejected",
            latest_bucket="rejected",
            current_state="active",
        ),
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
    return jobs


def parse_html(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    return BeautifulSoup(response.text, "html.parser")


def test_jobs_bucket_select_exposes_only_actionable_options(client, session):
    seed_ui_jobs(session)

    response = client.get("/jobs", headers={"accept": "text/html"})
    soup = parse_html(response)
    bucket_select = soup.find("select", {"name": "bucket"})

    assert bucket_select is not None
    options = [(option.get("value", ""), option.get_text(strip=True)) for option in bucket_select.find_all("option")]
    assert options == [("", "All actionable"), ("matched", "Matched"), ("review", "Review")]
    assert all(label != "Rejected" for _, label in options)
    assert all(value != "rejected" for value, _ in options)


def test_jobs_page_omits_rejected_rows_and_cards(client, session):
    seed_ui_jobs(session)

    response = client.get("/jobs", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "UI Matched Actionable" in response.text
    assert "UI Review Actionable" in response.text
    assert "UI Rejected Hidden" not in response.text
    assert "row-muted" not in response.text
    assert "job-card-muted" not in response.text
    assert "2 actionable job(s) found." in response.text


def test_manual_rejected_bucket_query_shows_actionable_empty_state(client, session):
    seed_ui_jobs(session)

    response = client.get("/jobs?bucket=rejected", headers={"accept": "text/html"})
    soup = parse_html(response)
    bucket_select = soup.find("select", {"name": "bucket"})

    assert "UI Rejected Hidden" not in response.text
    assert "No actionable jobs found" in response.text
    assert "Rejected jobs are hidden from this main view." in response.text
    assert bucket_select is not None
    assert bucket_select.find("option", {"value": "rejected"}) is None
    assert bucket_select.find("option", {"value": ""}).get_text(strip=True) == "All actionable"


def test_all_rejected_jobs_render_normal_empty_state(client, session):
    seed_ui_jobs(session)
    for job in session.query(JobPosting).all():
        job.latest_bucket = "rejected"
    session.commit()

    response = client.get("/jobs", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "No actionable jobs found" in response.text
    assert "UI Matched Actionable" not in response.text
    assert "UI Review Actionable" not in response.text
    assert "UI Rejected Hidden" not in response.text


def test_dashboard_does_not_render_rejected_actionable_card(client, session):
    seed_ui_jobs(session)

    response = client.get("/dashboard", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "UI Matched Actionable" in response.text
    assert "UI Review Actionable" in response.text
    assert "UI Rejected Hidden" not in response.text
    assert "/jobs?bucket=rejected" not in response.text
    assert "Rejected" not in response.text
