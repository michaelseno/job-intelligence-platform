from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry
from app.domain.ingestion import IngestionOrchestrator
from app.domain.notifications import NotificationService
from app.domain.operations import OperationsService
from app.domain.sources import SourceService
from app.domain.tracking import TrackingService, VALID_TRACKING_STATUSES
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
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

SOURCE_TYPE_HELP = {
    "greenhouse": "First-class MVP support. Requires the Greenhouse board token in external identifier.",
    "lever": "First-class MVP support. Requires the Lever company identifier in external identifier.",
    "common_pattern": "Visible for future expansion, but named common-pattern adapters remain parked as enhancements in this branch.",
    "custom_adapter": "Visible for future expansion, but custom adapters remain unsupported until explicitly approved and implemented.",
}


def get_session_dependency():
    yield from get_db_session()


def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept and "application/json" not in accept


def format_dt(value):
    if value is None:
        return "—"
    try:
        return value.strftime("%Y-%m-%d %H:%M UTC")
    except AttributeError:
        return str(value)


def format_date(value):
    if value is None:
        return "—"
    try:
        return value.strftime("%Y-%m-%d")
    except AttributeError:
        return str(value)


def with_message(url: str, level: str | None = None, message: str | None = None) -> str:
    if not level or not message:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["message_type"] = level
    query["message"] = message
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def redirect(url: str, status_code: int = status.HTTP_303_SEE_OTHER) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status_code)


def map_source_errors(errors: list[str]) -> dict[str, list[str]]:
    field_map: dict[str, list[str]] = defaultdict(list)
    for error in errors:
        if "name" in error:
            field_map["name"].append(error)
        elif "source_type" in error:
            field_map["source_type"].append(error)
        elif "base_url" in error:
            field_map["base_url"].append(error)
        elif "external_identifier" in error:
            field_map["external_identifier"].append(error)
        elif "adapter_key" in error:
            field_map["adapter_key"].append(error)
        else:
            field_map["__all__"].append(error)
    return dict(field_map)


def build_base_context(request: Request, session: Session) -> dict[str, Any]:
    latest_run = session.scalar(select(SourceRun).order_by(SourceRun.started_at.desc()))
    return {
        "request": request,
        "nav_items": [
            {"label": "Dashboard", "href": "/dashboard", "key": "dashboard"},
            {"label": "Jobs", "href": "/jobs", "key": "jobs"},
            {"label": "Sources", "href": "/sources", "key": "sources"},
            {"label": "Source Health", "href": "/source-health", "key": "source_health"},
            {"label": "Tracking", "href": "/tracking", "key": "tracking"},
            {"label": "Digest", "href": "/digest/latest", "key": "digest"},
            {"label": "Reminders", "href": "/reminders", "key": "reminders"},
        ],
        "flashes": [],
        "format_dt": format_dt,
        "format_date": format_date,
        "tracking_statuses": sorted(VALID_TRACKING_STATUSES),
        "latest_run_summary": latest_run,
        "message": request.query_params.get("message"),
        "message_type": request.query_params.get("message_type", "info"),
    }


def render(request: Request, session: Session, template_name: str, context: dict[str, Any], status_code: int = 200) -> HTMLResponse:
    full_context = build_base_context(request, session)
    full_context.update(context)
    return templates.TemplateResponse(request, template_name, full_context, status_code=status_code)


def get_primary_source_map(session: Session, jobs: list[JobPosting]) -> dict[int, Source | None]:
    links = list(session.scalars(select(JobSourceLink).where(JobSourceLink.job_posting_id.in_([job.id for job in jobs])))) if jobs else []
    source_ids = {link.source_id for link in links}
    sources = {source.id: source for source in session.scalars(select(Source).where(Source.id.in_(source_ids)))} if source_ids else {}
    by_job: dict[int, Source | None] = {}
    for job in jobs:
        primary = next((link for link in links if link.job_posting_id == job.id and link.is_primary), None)
        fallback = primary or next((link for link in links if link.job_posting_id == job.id), None)
        by_job[job.id] = sources.get(fallback.source_id) if fallback else None
    return by_job


def get_current_decision_map(session: Session, jobs: list[JobPosting]) -> dict[int, JobDecision | None]:
    decision_ids = [job.latest_decision_id for job in jobs if job.latest_decision_id]
    decisions = {decision.id: decision for decision in session.scalars(select(JobDecision).where(JobDecision.id.in_(decision_ids)))} if decision_ids else {}
    return {job.id: decisions.get(job.latest_decision_id) if job.latest_decision_id else None for job in jobs}


def get_pending_reminder_map(session: Session) -> dict[int, Reminder]:
    reminders = session.scalars(select(Reminder).where(Reminder.status == "pending").order_by(Reminder.due_at.asc()))
    result: dict[int, Reminder] = {}
    for reminder in reminders:
        result.setdefault(reminder.job_posting_id, reminder)
    return result


def to_job_card(job: JobPosting, source: Source | None, decision: JobDecision | None = None, reminder: Reminder | None = None) -> dict[str, Any]:
    reason = decision.decision_reason_summary if decision else "Classification details not available yet."
    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.company_name or source.name if source else "Unknown company",
        "source_name": source.name if source else "Unknown source",
        "source_id": source.id if source else None,
        "job_url": job.job_url,
        "location_text": job.location_text,
        "remote_type": job.remote_type,
        "current_state": job.current_state,
        "bucket": job.latest_bucket,
        "score": job.latest_score,
        "manual_keep": job.manual_keep,
        "tracking_status": job.tracking_status,
        "last_seen_at": job.last_seen_at,
        "last_ingested_at": job.last_ingested_at,
        "reason_summary": reason,
        "reminder": reminder,
    }


def build_jobs_query(bucket: str | None, tracking_status: str | None, source_id: int | None, search: str | None):
    query = select(JobPosting)
    if bucket:
        query = query.where(JobPosting.latest_bucket == bucket)
    if tracking_status:
        query = query.where(JobPosting.tracking_status == tracking_status)
    if search:
        like = f"%{search}%"
        query = query.where(or_(JobPosting.title.ilike(like), JobPosting.description_text.ilike(like), JobPosting.company_name.ilike(like)))
    return query, source_id


def sort_jobs(jobs: list[JobPosting], sort: str) -> list[JobPosting]:
    if sort == "highest_score":
        return sorted(jobs, key=lambda job: (job.latest_score or -9999, job.last_seen_at), reverse=True)
    if sort == "title":
        return sorted(jobs, key=lambda job: (job.title or "").lower())
    if sort == "company":
        return sorted(jobs, key=lambda job: (job.company_name or "").lower())
    return sorted(jobs, key=lambda job: job.last_seen_at, reverse=True)


def filter_jobs_by_source(session: Session, jobs: list[JobPosting], source_id: int | None) -> list[JobPosting]:
    if source_id is None:
        return jobs
    filtered: list[JobPosting] = []
    for job in jobs:
        link = session.scalar(select(JobSourceLink).where(JobSourceLink.job_posting_id == job.id, JobSourceLink.source_id == source_id))
        if link:
            filtered.append(job)
    return filtered


def serialize_job(job: JobPosting) -> JobResponse:
    return JobResponse.model_validate(job)


def build_source_page_context(
    request: Request,
    session: Session,
    registry: SourceAdapterRegistry,
    form_data: dict[str, Any] | None = None,
    form_errors: dict[str, list[str]] | None = None,
    import_result: SourceImportResponse | None = None,
    active_tab: str = "manual",
) -> dict[str, Any]:
    service = SourceService(session, registry)
    sources = service.list_sources()
    return {
        "page_key": "sources",
        "page_title": "Sources",
        "page_description": "Add Greenhouse or Lever sources manually, or import a batch from CSV.",
        "active_tab": active_tab,
        "sources": sources,
        "source_type_options": SOURCE_TYPE_HELP,
        "form_data": form_data or {
            "name": "",
            "source_type": "greenhouse",
            "company_name": "",
            "base_url": "",
            "external_identifier": "",
            "adapter_key": "",
            "notes": "",
            "is_active": True,
        },
        "form_errors": form_errors or {},
        "import_result": import_result,
    }


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session_dependency)):
    jobs = list(session.scalars(select(JobPosting)))
    reminders = list(session.scalars(select(Reminder).where(Reminder.status == "pending").order_by(Reminder.due_at.asc())))
    sources = list(session.scalars(select(Source).order_by(Source.name.asc())))
    if not wants_html(request):
        return {
            "matched_count": sum(1 for job in jobs if job.latest_bucket == "matched"),
            "review_count": sum(1 for job in jobs if job.latest_bucket == "review"),
            "rejected_count": sum(1 for job in jobs if job.latest_bucket == "rejected"),
            "saved_needing_action": sum(1 for job in jobs if job.tracking_status == "saved"),
            "applied_follow_ups": sum(1 for job in jobs if job.tracking_status == "applied"),
            "pending_reminders": len(reminders),
            "source_count": len(sources),
        }

    decisions = get_current_decision_map(session, jobs)
    primary_sources = get_primary_source_map(session, jobs)
    reminder_map = get_pending_reminder_map(session)
    matched_jobs = [to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder_map.get(job.id)) for job in sort_jobs([job for job in jobs if job.latest_bucket == "matched"], "newest")[:5]]
    review_jobs = [to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder_map.get(job.id)) for job in sort_jobs([job for job in jobs if job.latest_bucket == "review"], "newest")[:5]]
    source_warnings = [source for source in sources if source.health_state != "healthy" or source.last_run_status in {"failed", "partial_success"}]
    latest_digest = session.scalar(select(Digest).order_by(Digest.generated_at.desc()))
    return render(
        request,
        session,
        "dashboard/index.html",
        {
            "page_key": "dashboard",
            "summary": {
                "matched": sum(1 for job in jobs if job.latest_bucket == "matched"),
                "review": sum(1 for job in jobs if job.latest_bucket == "review"),
                "rejected": sum(1 for job in jobs if job.latest_bucket == "rejected"),
                "saved": sum(1 for job in jobs if job.tracking_status == "saved"),
                "applied": sum(1 for job in jobs if job.tracking_status == "applied"),
                "pending_reminders": len(reminders),
                "source_count": len(sources),
            },
            "matched_jobs": matched_jobs,
            "review_jobs": review_jobs,
            "reminders": reminders[:6],
            "reminder_jobs": {job.id: to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder_map.get(job.id)) for job in jobs if job.id in reminder_map},
            "source_warnings": source_warnings[:6],
            "sources": sources,
            "latest_digest": latest_digest,
            "has_jobs": bool(jobs),
        },
    )


@router.get("/sources")
def list_sources(
    request: Request,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    if wants_html(request):
        return render(request, session, "sources/index.html", build_source_page_context(request, session, registry))
    return SourceService(session, registry).list_sources()


@router.post("/sources", status_code=201)
async def create_source(
    request: Request,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    service = SourceService(session, registry)
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        payload = SourceCreateRequest(**(await request.json()))
        try:
            return service.create_source(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    form = await request.form()
    form_data = {
        "name": str(form.get("name", "")),
        "source_type": str(form.get("source_type", "greenhouse")),
        "company_name": str(form.get("company_name", "")),
        "base_url": str(form.get("base_url", "")),
        "external_identifier": str(form.get("external_identifier", "")),
        "adapter_key": str(form.get("adapter_key", "")),
        "notes": str(form.get("notes", "")),
        "is_active": form.get("is_active") == "on",
    }
    payload = SourceCreateRequest(
        name=form_data["name"],
        source_type=form_data["source_type"],
        company_name=form_data["company_name"] or None,
        base_url=form_data["base_url"],
        external_identifier=form_data["external_identifier"] or None,
        adapter_key=form_data["adapter_key"] or None,
        notes=form_data["notes"] or None,
        is_active=form_data["is_active"],
    )
    validation = service.validate(payload)
    if not validation.valid:
        return render(
            request,
            session,
            "sources/index.html",
            build_source_page_context(
                request,
                session,
                registry,
                form_data=form_data,
                form_errors=map_source_errors(validation.errors),
                active_tab="manual",
            ),
            status_code=400,
        )
    service.create_source(payload)
    return redirect(with_message("/sources", "success", "Source created. Greenhouse and Lever workflows are ready for ingestion."))


@router.post("/sources/import")
async def import_sources(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    payload = await file.read()
    result = SourceService(session, registry).import_csv(payload)
    if wants_html(request):
        return render(
            request,
            session,
            "sources/index.html",
            build_source_page_context(request, session, registry, import_result=result, active_tab="csv"),
        )
    return result


@router.get("/sources/{source_id}")
def get_source_detail(
    request: Request,
    source_id: int,
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    service = SourceService(session, registry)
    source = service.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    runs = list(session.scalars(select(SourceRun).where(SourceRun.source_id == source_id).order_by(SourceRun.started_at.desc())))
    if wants_html(request):
        return render(
            request,
            session,
            "sources/detail.html",
            {
                "page_key": "sources",
                "source": source,
                "runs": runs,
            },
        )
    return {"source": SourceResponse.model_validate(source), "runs": [SourceRunResponse.model_validate(run) for run in runs]}


@router.post("/sources/{source_id}/run")
def run_source(
    request: Request,
    source_id: int,
    next_url: str | None = Form(default=None),
    session: Session = Depends(get_session_dependency),
    registry: SourceAdapterRegistry = Depends(get_registry),
):
    source_service = SourceService(session, registry)
    source = source_service.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    run = IngestionOrchestrator(session, registry).run_source(source)
    if wants_html(request) or request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        if run.status in {"success", "partial_success"}:
            return redirect(with_message(next_url or f"/sources/{source_id}", "success", f"Ingestion finished for {source.name}: fetched {run.jobs_fetched_count} jobs."))
        else:
            return redirect(with_message(next_url or f"/sources/{source_id}", "error", f"Ingestion failed for {source.name}. Review source health for details."))
    return run


@router.get("/jobs")
def list_jobs(
    request: Request,
    bucket: str | None = Query(default=None),
    tracking_status: str | None = Query(default=None),
    source_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    session: Session = Depends(get_session_dependency),
):
    query, source_filter = build_jobs_query(bucket, tracking_status, source_id, search)
    jobs = list(session.scalars(query))
    jobs = filter_jobs_by_source(session, jobs, source_filter)
    jobs = sort_jobs(jobs, sort)
    if not wants_html(request):
        return jobs

    primary_sources = get_primary_source_map(session, jobs)
    decisions = get_current_decision_map(session, jobs)
    reminder_map = get_pending_reminder_map(session)
    job_cards = [to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder_map.get(job.id)) for job in jobs]
    sources = list(session.scalars(select(Source).order_by(Source.name.asc())))
    return render(
        request,
        session,
        "jobs/list.html",
        {
            "page_key": "jobs",
            "jobs": job_cards,
            "filters": {
                "bucket": bucket or "",
                "tracking_status": tracking_status or "",
                "source_id": str(source_id) if source_id else "",
                "search": search or "",
                "sort": sort,
            },
            "available_sources": sources,
        },
    )


@router.get("/jobs/{job_id}")
def get_job(request: Request, job_id: int, session: Session = Depends(get_session_dependency)):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    decision = None
    rule_rows: list[JobDecisionRule] = []
    if job.latest_decision_id:
        decision_row = session.get(JobDecision, job.latest_decision_id)
        rule_rows = list(session.scalars(select(JobDecisionRule).where(JobDecisionRule.job_decision_id == job.latest_decision_id)))
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
                for rule in rule_rows
            ],
        }
    links = list(session.scalars(select(JobSourceLink).where(JobSourceLink.job_posting_id == job_id)))
    events = TrackingService(session).list_events(job_id)
    if not wants_html(request):
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

    sources = {source.id: source for source in session.scalars(select(Source).where(Source.id.in_([link.source_id for link in links])))} if links else {}
    matched_rules = [rule for rule in rule_rows if rule.outcome == "matched"]
    negative_rules = [rule for rule in rule_rows if rule.outcome != "matched"]
    reminder = session.scalar(select(Reminder).where(Reminder.job_posting_id == job.id, Reminder.status == "pending").order_by(Reminder.due_at.asc()))
    return render(
        request,
        session,
        "jobs/detail.html",
        {
            "page_key": "jobs",
            "job": job,
            "decision": decision,
            "matched_rules": matched_rules,
            "negative_rules": negative_rules,
            "source_links": links,
            "sources": sources,
            "tracking_events": events,
            "reminder": reminder,
        },
    )


@router.post("/jobs/{job_id}/keep")
def keep_job(
    request: Request,
    job_id: int,
    next_url: str | None = Form(default=None),
    session: Session = Depends(get_session_dependency),
):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    updated = TrackingService(session).keep_job(job)
    if wants_html(request) or request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return redirect(with_message(next_url or f"/jobs/{job_id}", "success", "Job saved. Automated classification remains unchanged."))
    return updated


@router.post("/jobs/{job_id}/tracking-status")
async def update_tracking_status(job_id: int, request: Request, session: Session = Depends(get_session_dependency)):
    job = session.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    content_type = request.headers.get("content-type", "")
    next_url = None
    if content_type.startswith("application/json"):
        payload = TrackingStatusRequest(**(await request.json()))
    else:
        form = await request.form()
        next_url = form.get("next")
        payload = TrackingStatusRequest(
            tracking_status=str(form.get("tracking_status", "")),
            note_text=str(form.get("note_text", "")) or None,
        )

    try:
        updated = TrackingService(session).update_tracking_status(job, payload.tracking_status, payload.note_text)
    except ValueError as exc:
        if content_type.startswith("application/json"):
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return redirect(with_message(next_url or f"/jobs/{job_id}", "error", str(exc)))

    if wants_html(request) or not content_type.startswith("application/json"):
        return redirect(with_message(next_url or f"/jobs/{job_id}", "success", f"Tracking updated to {updated.tracking_status}."))
    return updated


@router.get("/source-health")
def source_health_page(request: Request, session: Session = Depends(get_session_dependency)):
    sources = OperationsService(session).list_source_health()
    return render(
        request,
        session,
        "ops/source_health.html",
        {
            "page_key": "source_health",
            "sources": sources,
        },
    )


@router.get("/ops/sources")
def source_health(request: Request, session: Session = Depends(get_session_dependency)):
    sources = OperationsService(session).list_source_health()
    if wants_html(request):
        return render(
            request,
            session,
            "ops/source_health.html",
            {
                "page_key": "source_health",
                "sources": sources,
            },
        )
    return sources


@router.get("/ops/runs")
def list_runs(request: Request, session: Session = Depends(get_session_dependency)):
    runs = OperationsService(session).list_runs()
    if wants_html(request):
        sources = {source.id: source for source in session.scalars(select(Source))}
        return render(request, session, "ops/run_list.html", {"page_key": "source_health", "runs": runs, "sources": sources})
    return runs


@router.get("/ops/runs/{run_id}")
def get_run(request: Request, run_id: int, session: Session = Depends(get_session_dependency)):
    run = OperationsService(session).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    if wants_html(request):
        source = session.get(Source, run.source_id)
        return render(request, session, "ops/run_detail.html", {"page_key": "source_health", "run": run, "source": source})
    return run


@router.get("/tracking")
def tracking_page(
    request: Request,
    tracking_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="last_updated"),
    session: Session = Depends(get_session_dependency),
):
    effective_status = tracking_status or "saved"
    query = select(JobPosting).where(JobPosting.tracking_status.is_not(None))
    if effective_status and effective_status != "all":
        query = query.where(JobPosting.tracking_status == effective_status)
    if search:
        like = f"%{search}%"
        query = query.where(or_(JobPosting.title.ilike(like), JobPosting.company_name.ilike(like), JobPosting.description_text.ilike(like)))
    jobs = list(session.scalars(query))
    reminder_map = get_pending_reminder_map(session)
    primary_sources = get_primary_source_map(session, jobs)
    decisions = get_current_decision_map(session, jobs)
    if sort == "urgency":
        jobs = sorted(jobs, key=lambda job: reminder_map.get(job.id).due_at if reminder_map.get(job.id) else job.last_seen_at)
    else:
        jobs = sorted(jobs, key=lambda job: job.last_seen_at, reverse=True)
    cards = [to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder_map.get(job.id)) for job in jobs]
    return render(
        request,
        session,
        "tracking/index.html",
        {
            "page_key": "tracking",
            "jobs": cards,
            "filters": {"tracking_status": effective_status, "search": search or "", "sort": sort},
        },
    )


@router.post("/digest/generate")
def generate_digest(request: Request, session: Session = Depends(get_session_dependency)):
    digest = NotificationService(session).generate_digest()
    items = list(session.scalars(select(DigestItem).where(DigestItem.digest_id == digest.id)))
    if wants_html(request) or request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return redirect(with_message("/digest/latest", "success", "Digest generated from newly eligible matched and review jobs."))
    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date,
        status=digest.status,
        generated_at=digest.generated_at,
        delivery_channel=digest.delivery_channel,
        content_summary=digest.content_summary,
        items=[DigestItemResponse(job_posting_id=item.job_posting_id, bucket=item.bucket, reason=item.reason) for item in items],
    )


@router.get("/digest/latest")
def latest_digest(request: Request, session: Session = Depends(get_session_dependency)):
    digest = session.scalar(select(Digest).order_by(Digest.generated_at.desc()))
    if digest is None:
        if wants_html(request):
            return render(request, session, "notifications/digest.html", {"page_key": "digest", "digest": None, "grouped_items": {}})
        return None
    items = list(session.scalars(select(DigestItem).where(DigestItem.digest_id == digest.id)))
    if wants_html(request):
        jobs = {job.id: job for job in session.scalars(select(JobPosting).where(JobPosting.id.in_([item.job_posting_id for item in items])))} if items else {}
        primary_sources = get_primary_source_map(session, list(jobs.values()))
        decisions = get_current_decision_map(session, list(jobs.values()))
        grouped_items: dict[str, list[dict[str, Any]]] = {"matched": [], "review": []}
        for item in items:
            job = jobs.get(item.job_posting_id)
            if job is None:
                continue
            grouped_items[item.bucket].append({"item": item, "job": to_job_card(job, primary_sources.get(job.id), decisions.get(job.id))})
        return render(request, session, "notifications/digest.html", {"page_key": "digest", "digest": digest, "grouped_items": grouped_items})
    return DigestResponse(
        id=digest.id,
        digest_date=digest.digest_date,
        status=digest.status,
        generated_at=digest.generated_at,
        delivery_channel=digest.delivery_channel,
        content_summary=digest.content_summary,
        items=[DigestItemResponse(job_posting_id=item.job_posting_id, bucket=item.bucket, reason=item.reason) for item in items],
    )


@router.post("/reminders/generate")
def generate_reminders(request: Request, session: Session = Depends(get_session_dependency)):
    reminders = NotificationService(session).generate_reminders()
    if wants_html(request) or request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return redirect(with_message("/reminders", "success", f"Generated {len(reminders)} reminder(s)."))
    return [ReminderResponse.model_validate(reminder) for reminder in reminders]


@router.get("/reminders")
def list_reminders(request: Request, session: Session = Depends(get_session_dependency)):
    reminders = list(session.scalars(select(Reminder).order_by(Reminder.due_at.asc())))
    if not wants_html(request):
        return [ReminderResponse.model_validate(reminder) for reminder in reminders]
    jobs = {job.id: job for job in session.scalars(select(JobPosting).where(JobPosting.id.in_([reminder.job_posting_id for reminder in reminders])))} if reminders else {}
    primary_sources = get_primary_source_map(session, list(jobs.values()))
    decisions = get_current_decision_map(session, list(jobs.values()))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for reminder in reminders:
        job = jobs.get(reminder.job_posting_id)
        if job is None:
            continue
        grouped[reminder.status].append({"reminder": reminder, "job": to_job_card(job, primary_sources.get(job.id), decisions.get(job.id), reminder)})
    return render(request, session, "notifications/reminders.html", {"page_key": "reminders", "grouped_reminders": dict(grouped)})


@router.post("/reminders/{reminder_id}/dismiss")
def dismiss_reminder(
    request: Request,
    reminder_id: int,
    next_url: str | None = Form(default=None),
    session: Session = Depends(get_session_dependency),
):
    reminder = NotificationService(session).dismiss_reminder(reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    if wants_html(request) or request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        return redirect(with_message(next_url or "/reminders", "success", "Reminder dismissed."))
    return ReminderResponse.model_validate(reminder)
