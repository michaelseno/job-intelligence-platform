from __future__ import annotations

from datetime import timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.domain.common import utcnow
from app.domain.job_visibility import apply_visible_jobs, visible_job_predicate
from app.persistence.models import Digest, DigestItem, JobDecision, JobPosting, JobTrackingEvent, Reminder


class NotificationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def generate_digest(self) -> Digest:
        now = utcnow()
        digest = self.session.scalar(
            select(Digest).where(Digest.digest_date == now.date(), Digest.delivery_channel == "in_app")
        )
        if digest is None:
            digest = Digest(
                digest_date=now.date(),
                status="generated",
                generated_at=now,
                delivery_channel="in_app",
                content_summary="",
            )
            self.session.add(digest)
            self.session.flush()
        prior = self.session.scalar(
            select(Digest).where(Digest.generated_at < digest.generated_at).order_by(Digest.generated_at.desc())
        )
        window_start = prior.generated_at if prior else now - timedelta(days=1)
        decisions = list(
            self.session.scalars(
                select(JobDecision)
                .join(JobPosting, JobPosting.id == JobDecision.job_posting_id)
                .where(
                    JobDecision.is_current.is_(True),
                    JobDecision.bucket.in_(["matched", "review"]),
                    JobDecision.created_at >= window_start,
                    JobDecision.created_at <= now,
                    visible_job_predicate(),
                )
            )
        )
        summary_parts: list[str] = []
        for decision in decisions:
            existing = self.session.scalar(
                select(DigestItem).where(DigestItem.digest_id == digest.id, DigestItem.job_posting_id == decision.job_posting_id)
            )
            if existing:
                continue
            reason = "new_matched" if decision.bucket == "matched" else "new_review"
            self.session.add(DigestItem(digest_id=digest.id, job_posting_id=decision.job_posting_id, bucket=decision.bucket, reason=reason))
            summary_parts.append(reason)
        digest.content_summary = f"{summary_parts.count('new_matched')} matched, {summary_parts.count('new_review')} review"
        self.session.add(digest)
        self.session.commit()
        self.session.refresh(digest)
        return digest

    def generate_reminders(self) -> list[Reminder]:
        now = utcnow()
        jobs = list(
            self.session.scalars(
                apply_visible_jobs(select(JobPosting)).where(JobPosting.tracking_status.in_(["saved", "applied"]))
            )
        )
        reminders: list[Reminder] = []
        for job in jobs:
            latest_event = self.session.scalar(
                select(JobTrackingEvent)
                .where(JobTrackingEvent.job_posting_id == job.id)
                .order_by(JobTrackingEvent.created_at.desc())
            )
            if latest_event is None:
                continue
            due_at = None
            reminder_type = None
            if job.tracking_status == "saved":
                due_at = _ensure_aware(latest_event.created_at) + timedelta(days=self.settings.saved_reminder_days)
                reminder_type = "saved_follow_up"
            elif job.tracking_status == "applied":
                due_at = _ensure_aware(latest_event.created_at) + timedelta(days=self.settings.applied_reminder_days)
                reminder_type = "applied_follow_up"
            if not reminder_type or due_at is None or due_at > now:
                continue
            existing = self.session.scalar(
                select(Reminder).where(
                    Reminder.job_posting_id == job.id,
                    Reminder.reminder_type == reminder_type,
                    Reminder.status == "pending",
                )
            )
            if existing:
                reminders.append(existing)
                continue
            reminder = Reminder(job_posting_id=job.id, reminder_type=reminder_type, due_at=due_at, status="pending", generated_at=now)
            self.session.add(reminder)
            reminders.append(reminder)
        self.session.commit()
        return reminders

    def dismiss_reminder(self, reminder_id: int) -> Reminder | None:
        reminder = self.session.get(Reminder, reminder_id)
        if reminder is None:
            return None
        reminder.status = "dismissed"
        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)
        return reminder


def _ensure_aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
