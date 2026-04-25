from __future__ import annotations

from datetime import timedelta

from app.domain.notifications import NotificationService
from app.persistence.models import Digest, DigestItem, JobDecision, JobPosting, JobTrackingEvent, Reminder, Source, utcnow


def test_dashboard_tracking_reminders_and_digest_hide_pending_cleanup_jobs(client, session):
    source = Source(name="Deleted Surface", source_type="greenhouse", base_url="https://boards.greenhouse.io/deleted-surface", external_identifier="deleted-surface", dedupe_key="deleted-surface", is_active=False, deleted_at=utcnow())
    session.add(source)
    session.commit()
    retained = JobPosting(canonical_key="surface-retained", primary_source_id=source.id, title="Surface Retained", job_url="https://example.com/surface-retained", latest_bucket="matched", current_state="active", tracking_status="saved")
    hidden = JobPosting(canonical_key="surface-hidden", primary_source_id=source.id, title="Surface Hidden", job_url="https://example.com/surface-hidden", latest_bucket="review", current_state="active", tracking_status="saved")
    session.add_all([retained, hidden])
    session.flush()
    old = utcnow() - timedelta(days=10)
    session.add_all([
        JobTrackingEvent(job_posting_id=retained.id, event_type="status_change", tracking_status="saved", created_at=old),
        JobTrackingEvent(job_posting_id=hidden.id, event_type="status_change", tracking_status="saved", created_at=old),
        Reminder(job_posting_id=retained.id, reminder_type="saved_follow_up", due_at=old, status="pending"),
        Reminder(job_posting_id=hidden.id, reminder_type="saved_follow_up", due_at=old, status="pending"),
    ])
    digest = Digest(digest_date=utcnow().date(), status="generated", delivery_channel="in_app", content_summary="")
    session.add(digest)
    session.flush()
    session.add_all([
        DigestItem(digest_id=digest.id, job_posting_id=retained.id, bucket="matched", reason="new_matched"),
        DigestItem(digest_id=digest.id, job_posting_id=hidden.id, bucket="review", reason="new_review"),
    ])
    session.commit()

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["matched_count"] == 1
    assert dashboard.json()["review_count"] == 0
    assert dashboard.json()["pending_reminders"] == 1

    tracking = client.get("/tracking", headers={"accept": "text/html"})
    assert tracking.status_code == 200
    assert "Surface Retained" in tracking.text
    assert "Surface Hidden" not in tracking.text

    reminders = client.get("/reminders")
    assert reminders.status_code == 200
    assert [reminder["job_posting_id"] for reminder in reminders.json()] == [retained.id]

    digest_response = client.get("/digest/latest")
    assert digest_response.status_code == 200
    assert [item["job_posting_id"] for item in digest_response.json()["items"]] == [retained.id]


def test_notification_generation_excludes_pending_cleanup_jobs(session):
    source = Source(name="Deleted Generation", source_type="greenhouse", base_url="https://boards.greenhouse.io/deleted-generation", external_identifier="deleted-generation", dedupe_key="deleted-generation", is_active=False, deleted_at=utcnow())
    session.add(source)
    session.commit()
    hidden = JobPosting(canonical_key="gen-hidden", primary_source_id=source.id, title="Gen Hidden", job_url="https://example.com/gen-hidden", latest_bucket="review", current_state="active", tracking_status="saved")
    session.add(hidden)
    session.flush()
    session.add(JobDecision(job_posting_id=hidden.id, decision_version="v1", bucket="review", final_score=50, sponsorship_state="unknown", decision_reason_summary="summary", is_current=True))
    session.add(JobTrackingEvent(job_posting_id=hidden.id, event_type="status_change", tracking_status="saved", created_at=utcnow() - timedelta(days=10)))
    session.commit()

    digest = NotificationService(session).generate_digest()
    reminders = NotificationService(session).generate_reminders()

    assert digest.content_summary == "0 matched, 0 review"
    assert reminders == []
