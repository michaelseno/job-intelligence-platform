from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SourceCreateRequest(BaseModel):
    name: str
    source_type: str
    base_url: str
    external_identifier: str | None = None
    adapter_key: str | None = None
    company_name: str | None = None
    is_active: bool = True
    notes: str | None = None
    config_json: dict | None = None


class SourceUpdateRequest(BaseModel):
    name: str | None = None
    source_type: str | None = None
    base_url: str | None = None
    external_identifier: str | None = None
    adapter_key: str | None = None
    company_name: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    adapter_key: str | None
    company_name: str | None
    base_url: str
    external_identifier: str | None
    notes: str | None
    is_active: bool
    deleted_at: datetime | None
    last_run_at: datetime | None
    last_run_status: str | None
    last_jobs_fetched_count: int
    consecutive_empty_runs: int
    health_state: str
    health_message: str | None

    model_config = {"from_attributes": True}


class SourceImportRowResult(BaseModel):
    row_number: int
    status: str
    message: str
    source_id: int | None = None


class SourceImportResponse(BaseModel):
    created: int
    skipped_duplicate: int
    invalid: int
    rows: list[SourceImportRowResult]


class SourceDeleteImpactResponse(BaseModel):
    source_id: int
    source_name: str
    run_count: int
    linked_job_count: int
    tracked_job_count: int
    has_run_history: bool
    has_linked_jobs: bool


class SourceDeleteResponse(BaseModel):
    deleted: bool
    source_id: int
    deleted_at: datetime
    cleanup_queued: bool = False
    cleanup_status: str | None = None


class SourceRunResponse(BaseModel):
    id: int
    source_id: int
    trigger_type: str
    status: str
    jobs_fetched_count: int
    jobs_created_count: int
    jobs_updated_count: int
    jobs_unchanged_count: int
    error_count: int
    warning_count: int
    empty_result_flag: bool
    log_summary: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class SourceBatchRunPreviewRequest(BaseModel):
    mode: Literal["all", "selected"]
    source_ids: list[int] | None = None

    @model_validator(mode="after")
    def validate_selected_source_ids(self):
        if self.mode == "selected" and not self.source_ids:
            raise ValueError("source_ids is required for selected batch runs.")
        return self


class SourceBatchRunStartRequest(BaseModel):
    preview_id: str
    job_preferences: dict


class SourceBatchSourceRef(BaseModel):
    source_id: int
    source_name: str
    health_state: str


class SourceBatchSkippedSource(BaseModel):
    source_id: int
    source_name: str
    health_state: str | None = None
    reason: str


class SourceBatchSourceResult(BaseModel):
    source_id: int
    source_name: str
    status: str
    attempts_used: int
    source_run_ids: list[int]
    last_error: str | None = None


class SourceBatchRunPreviewResponse(BaseModel):
    preview_id: str
    mode: Literal["all", "selected"]
    eligible_count: int
    skipped_count: int
    eligible_sources: list[SourceBatchSourceRef]
    skipped_sources: list[SourceBatchSkippedSource]
    expires_at: datetime


class SourceBatchRunStartResponse(BaseModel):
    batch_id: str
    status: str
    mode: Literal["all", "selected"]
    eligible_count: int
    skipped_count: int
    poll_url: str


class SourceBatchRunStatusResponse(BaseModel):
    batch_id: str
    mode: Literal["all", "selected"]
    status: str
    eligible_count: int
    skipped_count: int
    success_count: int
    failure_count: int
    pending_count: int
    running_count: int
    completed_count: int
    started_at: datetime | None
    finished_at: datetime | None
    source_results: list[SourceBatchSourceResult]
    skipped_sources: list[SourceBatchSkippedSource]
    error_message: str | None = None


class DecisionRuleResponse(BaseModel):
    rule_key: str
    rule_category: str
    outcome: str
    score_delta: int
    evidence_snippet: str | None
    evidence_field: str | None
    explanation_text: str


class DecisionResponse(BaseModel):
    id: int
    bucket: str
    final_score: int
    sponsorship_state: str
    decision_reason_summary: str
    created_at: datetime
    rules: list[DecisionRuleResponse]


class JobResponse(BaseModel):
    id: int
    title: str
    company_name: str | None
    job_url: str
    location_text: str | None
    remote_type: str | None
    employment_type: str | None
    current_state: str
    latest_bucket: str | None
    latest_score: int | None
    manual_keep: bool
    tracking_status: str | None
    first_seen_at: datetime
    last_seen_at: datetime
    last_ingested_at: datetime

    model_config = {"from_attributes": True}


class JobDetailResponse(JobResponse):
    description_text: str | None
    sponsorship_text: str | None
    decision: DecisionResponse | None = None
    source_links: list[dict] = Field(default_factory=list)
    tracking_events: list[dict] = Field(default_factory=list)


class TrackingStatusRequest(BaseModel):
    tracking_status: str
    note_text: str | None = None


class DigestItemResponse(BaseModel):
    job_posting_id: int
    bucket: str
    reason: str


class DigestResponse(BaseModel):
    id: int
    digest_date: date
    status: str
    generated_at: datetime
    delivery_channel: str
    content_summary: str
    items: list[DigestItemResponse]


class ReminderResponse(BaseModel):
    id: int
    job_posting_id: int
    reminder_type: str
    due_at: datetime
    status: str
    generated_at: datetime

    model_config = {"from_attributes": True}
