from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.ingestion import IngestionOrchestrator
from app.domain.notifications import NotificationService
from app.domain.operations import OperationsService
from app.domain.sources import SourceService
from app.domain.tracking import TrackingService
from app.persistence.db import get_db_session
from app.persistence.models import Digest, DigestItem, JobDecision, JobDecisionRule, JobPosting, JobSourceLink, Reminder, Source, SourceRun
from app.schemas import (
    DigestItemResponse,
    DigestResponse,
    JobDetailResponse,
    JobResponse,
    ReminderResponse,
    SourceCreateRequest,
    SourceImportResponse,
    SourceResponse,
    SourceRunResponse,
    TrackingStatusRequest,
)
from app.web.dependencies import get_registry

router = APIRouter()


def get_session_dependency():
    yield from get_db_session()


@router.get("/")
def dashboard(session: Session = Depends(get_session_dependency)) -> dict:
    jobs = list(session.scalars(select(JobPosting)))
    reminders = list(session.scalars(select(Reminder).where(Reminder.status == "pending")))
    sources = list(session.scalars(select(Source)))
    return {
        "matched_count": sum(1 for job in jobs if job.latest_bucket == "matched"),
        "review_count": sum(1 for job in jobs if job.latest_bucket == "review"),
        "rejected_count": sum(1 for job in jobs if job.latest_bucket == "rejected"),
        "saved_needing_action": sum(1 for job in jobs if job.tracking_status == "saved"),
        "applied_follow_ups": sum(1 for job in jobs if job.tracking_status == "applied"),
        "pending_reminders": len(reminders),
        "source_count": len(sources),
    }


@router.get("/sources", response_model=list[SourceResponse])
def list_sources(
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    return SourceService(session, registry).list_sources()


@router.post("/sources", response_model=SourceResponse, status_code=201)
def create_source(
    payload: SourceCreateRequest,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    try:
        return SourceService(session, registry).create_source(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sources/import", response_model=SourceImportResponse)
async def import_sources(
    file: UploadFile = File(...),
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    payload = await file.read()
    return SourceService(session, registry).import_csv(payload)


@router.get("/sources/{source_id}")
def get_source_detail(
    source_id: int,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    service = SourceService(session, registry)
    source = service.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    runs = list(session.scalars(select(SourceRun).where(SourceRun.source_id == source_id).order_by(SourceRun.started_at.desc())))
    return {"source": SourceResponse.model_validate(source), "runs": [SourceRunResponse.model_validate(run) for run in runs]}


@router.post("/sources/{source_id}/run", response_model=SourceRunResponse)
def run_source(
    source_id: int,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    source_service = SourceService(session, registry)
    source = source_service.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    run = IngestionOrchestrator(session, registry).run_source(source)
    return run


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    bucket: str | None = Query(default=None),
    tracking_status: str | None = Query(default=None),
    source_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    session: Session = Depends(get_session_dependency),
):
    query = select(JobPosting)
    if bucket:
        query = query.where(JobPosting.latest_bucket == bucket)
    if tracking_status:
        query = query.where(JobPosting.tracking_status == tracking_status)
    if search:
        like = f"%{search}%"
        query = query.where(or_(JobPosting.title.ilike(like), JobPosting.description_text.ilike(like), JobPosting.company_name.ilike(like)))
    jobs = list(session.scalars(query.order_by(JobPosting.last_seen_at.desc())))
    if source_id is not None:
        filtered = []
        for job in jobs:
            link = session.scalar(select(JobSourceLink).where(JobSourceLink.job_posting_id == job.id, JobSourceLink.source_id == source_id))
            if link:
                filtered.append(job)
        jobs = filtered
    return jobs


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int, session: Session = Depends(get_session_dependency)):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    decision = None
    if job.latest_decision_id:
        decision_row = session.get(JobDecision, job.latest_decision_id)
        rules = list(session.scalars(select(JobDecisionRule).where(JobDecisionRule.job_decision_id == job.latest_decision_id)))
        decision = {
            "id": decision_row.id,
            "bucket": decision_row.bucket,
            "final_score": decision_row.final_score,
            "sponsorship_state": decision_row.sponsorship_state,
            "decision_reason_summary": decision_row.decision_reason_summary,
            "created_at": decision_row.created_at,
            "rules": [
                {
                    "rule_key": rule.rule_key,
                    "rule_category": rule.rule_category,
                    "outcome": rule.outcome,
                    "score_delta": rule.score_delta,
                    "evidence_snippet": rule.evidence_snippet,
                    "evidence_field": rule.evidence_field,
                    "explanation_text": rule.explanation_text,
                }
                for rule in rules
            ],
        }
    links = list(session.scalars(select(JobSourceLink).where(JobSourceLink.job_posting_id == job_id)))
    from app.domain.tracking import TrackingService
    events = TrackingService(session).list_events(job_id)
    return {
        **JobResponse.model_validate(job).model_dump(),
        "description_text": job.description_text,
        "sponsorship_text": job.sponsorship_text,
        "decision": decision,
        "source_links": [
            {
                "source_id": link.source_id,
                "source_run_id": link.source_run_id,
                "external_job_id": link.external_job_id,
                "source_job_url": link.source_job_url,
                "last_seen_at": link.last_seen_at,
            }
            for link in links
        ],
        "tracking_events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "tracking_status": event.tracking_status,
                "note_text": event.note_text,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }


@router.post("/jobs/{job_id}/keep", response_model=JobResponse)
def keep_job(job_id: int, session: Session = Depends(get_session_dependency)):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return TrackingService(session).keep_job(job)


@router.post("/jobs/{job_id}/tracking-status", response_model=JobResponse)
def update_tracking_status(job_id: int, payload: TrackingStatusRequest, session: Session = Depends(get_session_dependency)):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        return TrackingService(session).update_tracking_status(job, payload.tracking_status, payload.note_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ops/sources", response_model=list[SourceResponse])
def source_health(session: Session = Depends(get_session_dependency)):
    return OperationsService(session).list_source_health()


@router.get("/ops/runs", response_model=list[SourceRunResponse])
def list_runs(session: Session = Depends(get_session_dependency)):
    return OperationsService(session).list_runs()


@router.get("/ops/runs/{run_id}", response_model=SourceRunResponse)
def get_run(run_id: int, session: Session = Depends(get_session_dependency)):
    run = OperationsService(session).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


@router.post("/digest/generate", response_model=DigestResponse)
def generate_digest(session: Session = Depends(get_session_dependency)):
    digest = NotificationService(session).generate_digest()
    items = list(session.scalars(select(DigestItem).where(DigestItem.digest_id == digest.id)))
    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date,
        status=digest.status,
        generated_at=digest.generated_at,
        delivery_channel=digest.delivery_channel,
        content_summary=digest.content_summary,
        items=[DigestItemResponse(job_posting_id=item.job_posting_id, bucket=item.bucket, reason=item.reason) for item in items],
    )


@router.get("/digest/latest", response_model=DigestResponse | None)
def latest_digest(session: Session = Depends(get_session_dependency)):
    digest = session.scalar(select(Digest).order_by(Digest.generated_at.desc()))
    if digest is None:
        return None
    items = list(session.scalars(select(DigestItem).where(DigestItem.digest_id == digest.id)))
    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date,
        status=digest.status,
        generated_at=digest.generated_at,
        delivery_channel=digest.delivery_channel,
        content_summary=digest.content_summary,
        items=[DigestItemResponse(job_posting_id=item.job_posting_id, bucket=item.bucket, reason=item.reason) for item in items],
    )


@router.post("/reminders/generate", response_model=list[ReminderResponse])
def generate_reminders(session: Session = Depends(get_session_dependency)):
    reminders = NotificationService(session).generate_reminders()
    return [ReminderResponse.model_validate(reminder) for reminder in reminders]


@router.get("/reminders", response_model=list[ReminderResponse])
def list_reminders(session: Session = Depends(get_session_dependency)):
    reminders = list(session.scalars(select(Reminder).order_by(Reminder.due_at.asc())))
    return [ReminderResponse.model_validate(reminder) for reminder in reminders]


@router.post("/reminders/{reminder_id}/dismiss", response_model=ReminderResponse)
def dismiss_reminder(reminder_id: int, session: Session = Depends(get_session_dependency)):
    reminder = NotificationService(session).dismiss_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return ReminderResponse.model_validate(reminder)
