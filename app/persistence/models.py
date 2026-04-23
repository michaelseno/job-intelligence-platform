from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50))
    adapter_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_url: Mapped[str] = mapped_column(String(1024))
    external_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(1024), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_jobs_fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_empty_runs: Mapped[int] = mapped_column(Integer, default=0)
    health_state: Mapped[str] = mapped_column(String(50), default="healthy")
    health_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    runs: Mapped[list[SourceRun]] = relationship(back_populates="source")


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    trigger_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jobs_fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    jobs_created_count: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated_count: Mapped[int] = mapped_column(Integer, default=0)
    jobs_unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    empty_result_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    log_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source: Mapped[Source] = relationship(back_populates="runs")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(255), unique=True)
    primary_source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(String(500))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_url: Mapped[str] = mapped_column(String(2048))
    normalized_job_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    sponsorship_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    current_state: Mapped[str] = mapped_column(String(50), default="active")
    latest_bucket: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latest_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latest_decision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_keep: Mapped[bool] = mapped_column(Boolean, default=False)
    tracking_status: Mapped[str | None] = mapped_column(String(50), nullable=True)


class JobSourceLink(Base):
    __tablename__ = "job_source_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    source_run_id: Mapped[int] = mapped_column(ForeignKey("source_runs.id"))
    external_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_job_url: Mapped[str] = mapped_column(String(2048))
    raw_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JobDecision(Base):
    __tablename__ = "job_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    decision_version: Mapped[str] = mapped_column(String(50))
    bucket: Mapped[str] = mapped_column(String(50))
    final_score: Mapped[int] = mapped_column(Integer)
    sponsorship_state: Mapped[str] = mapped_column(String(50))
    decision_reason_summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class JobDecisionRule(Base):
    __tablename__ = "job_decision_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_decision_id: Mapped[int] = mapped_column(ForeignKey("job_decisions.id"))
    rule_key: Mapped[str] = mapped_column(String(100))
    rule_category: Mapped[str] = mapped_column(String(50))
    outcome: Mapped[str] = mapped_column(String(50))
    score_delta: Mapped[int] = mapped_column(Integer)
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_field: Mapped[str | None] = mapped_column(String(50), nullable=True)
    explanation_text: Mapped[str] = mapped_column(Text)


class JobTrackingEvent(Base):
    __tablename__ = "job_tracking_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    tracking_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digest_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    delivery_channel: Mapped[str] = mapped_column(String(50))
    content_summary: Mapped[str] = mapped_column(Text)


class DigestItem(Base):
    __tablename__ = "digest_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digests.id"))
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    bucket: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(String(50))


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    reminder_type: Mapped[str] = mapped_column(String(50))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
