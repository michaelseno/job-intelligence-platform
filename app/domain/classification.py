from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.domain.common import clean_text, evidence_snippet
from app.persistence.models import JobDecision, JobDecisionRule, JobPosting


@dataclass
class RuleResult:
    rule_key: str
    rule_category: str
    outcome: str
    score_delta: int
    evidence_snippet: str | None
    evidence_field: str | None
    explanation_text: str


ROLE_POSITIVES = {
    "python backend": ["python backend", "backend engineer", "backend developer", "python engineer"],
    "sdet": ["sdet", "software development engineer in test"],
    "qa automation": ["qa automation", "quality assurance automation", "test automation"],
    "test infrastructure": ["test infrastructure", "testing platform", "quality platform"],
    "developer productivity": ["developer productivity", "developer experience", "engineering productivity"],
}
ROLE_NEGATIVES = ["sales", "account executive", "marketing", "recruiter", "designer", "hr", "finance"]
REMOTE_POSITIVES = ["remote", "work from anywhere", "distributed"]
SPAIN_POSITIVES = ["spain", "barcelona", "madrid"]
LOCATION_NEGATIVES = ["on-site", "onsite", "must be located in", "us only"]
SPONSORSHIP_UNSUPPORTED = ["no visa sponsorship", "unable to sponsor", "must be authorized to work"]
SPONSORSHIP_SUPPORTED = ["visa sponsorship available", "sponsorship available", "will sponsor"]
SPONSORSHIP_AMBIGUOUS = ["visa", "work authorization", "sponsorship"]


class ClassificationService:
    decision_version = "mvp_v1"

    def __init__(self, session: Session) -> None:
        self.session = session

    def classify_job(self, job: JobPosting) -> JobDecision:
        text = " ".join(filter(None, [job.title, job.location_text, job.description_text, job.sponsorship_text]))
        lower = clean_text(text).lower()
        rules: list[RuleResult] = []
        score = 0

        for family, keywords in ROLE_POSITIVES.items():
            for keyword in keywords:
                if keyword in lower:
                    rules.append(
                        RuleResult(
                            rule_key=family.replace(" ", "_"),
                            rule_category="role_positive",
                            outcome="matched",
                            score_delta=18,
                            evidence_snippet=evidence_snippet(job.title + " " + (job.description_text or ""), keyword),
                            evidence_field="title_description",
                            explanation_text=f"Role aligns with {family} target.",
                        )
                    )
                    score += 18
                    break

        for keyword in ROLE_NEGATIVES:
            if keyword in lower:
                rules.append(
                    RuleResult(
                        rule_key=f"negative_{keyword.replace(' ', '_')}",
                        rule_category="role_negative",
                        outcome="negative",
                        score_delta=-25,
                        evidence_snippet=evidence_snippet(text, keyword),
                        evidence_field="title_description",
                        explanation_text=f"Role appears unrelated because it mentions {keyword}.",
                    )
                )
                score -= 25
                break

        if any(keyword in lower for keyword in REMOTE_POSITIVES):
            rules.append(RuleResult("remote_preferred", "location_positive", "matched", 10, evidence_snippet(text, "remote"), "location_text", "Role indicates remote availability."))
            score += 10
        elif any(keyword in lower for keyword in SPAIN_POSITIVES):
            rules.append(RuleResult("spain_preferred", "location_positive", "matched", 6, evidence_snippet(text, "spain") or evidence_snippet(text, "madrid") or evidence_snippet(text, "barcelona"), "location_text", "Role matches Spain secondary preference."))
            score += 6

        location_negative = False
        for keyword in LOCATION_NEGATIVES:
            if keyword in lower:
                location_negative = True
                rules.append(RuleResult("location_incompatible", "location_negative", "negative", -12, evidence_snippet(text, keyword), "location_text", "Location appears incompatible with MVP preferences."))
                score -= 12
                break

        sponsorship_state = "missing"
        if any(keyword in lower for keyword in SPONSORSHIP_SUPPORTED):
            sponsorship_state = "supported"
            rules.append(RuleResult("sponsorship_supported", "sponsorship", "matched", 6, evidence_snippet(text, "sponsorship") or evidence_snippet(text, "visa"), "sponsorship_text", "Posting indicates sponsorship support."))
            score += 6
        elif any(keyword in lower for keyword in SPONSORSHIP_UNSUPPORTED):
            sponsorship_state = "unsupported"
            rules.append(RuleResult("sponsorship_unsupported", "sponsorship", "negative", -20, evidence_snippet(text, "sponsor") or evidence_snippet(text, "authorized"), "sponsorship_text", "Posting indicates sponsorship is not supported."))
            score -= 20
        elif any(keyword in lower for keyword in SPONSORSHIP_AMBIGUOUS):
            sponsorship_state = "ambiguous"
            rules.append(RuleResult("sponsorship_ambiguous", "sponsorship", "override", 0, evidence_snippet(text, "sponsorship") or evidence_snippet(text, "visa") or evidence_snippet(text, "authorization"), "sponsorship_text", "Sponsorship is mentioned but not resolved clearly."))

        if len(clean_text(job.description_text)) < 120:
            rules.append(RuleResult("low_text_confidence", "quality", "informational", -2, None, None, "Limited source text reduced confidence."))
            score -= 2

        positive_role = any(rule.rule_category == "role_positive" for rule in rules)
        explicit_role_negative = any(rule.rule_category == "role_negative" for rule in rules)

        if explicit_role_negative and score < 10:
            bucket = "rejected"
            summary = "Rejected due to clear role mismatch."
        elif sponsorship_state in {"ambiguous", "missing"} and positive_role:
            bucket = "review"
            summary = "Review because sponsorship is unclear or missing despite role alignment."
        elif sponsorship_state == "unsupported" and positive_role:
            bucket = "rejected"
            summary = "Rejected because sponsorship is explicitly unsupported."
        elif positive_role and not location_negative and score >= 25:
            bucket = "matched"
            summary = "Matched due to role alignment and acceptable location signal."
        elif positive_role:
            bucket = "review"
            summary = "Review due to mixed confidence or incomplete constraints."
        else:
            bucket = "rejected"
            summary = "Rejected because the role did not align with target role families."

        self.session.execute(update(JobDecision).where(JobDecision.job_posting_id == job.id).values(is_current=False))
        decision = JobDecision(
            job_posting_id=job.id,
            decision_version=self.decision_version,
            bucket=bucket,
            final_score=score,
            sponsorship_state=sponsorship_state,
            decision_reason_summary=summary,
            is_current=True,
        )
        self.session.add(decision)
        self.session.flush()
        for rule in rules:
            self.session.add(
                JobDecisionRule(
                    job_decision_id=decision.id,
                    rule_key=rule.rule_key,
                    rule_category=rule.rule_category,
                    outcome=rule.outcome,
                    score_delta=rule.score_delta,
                    evidence_snippet=rule.evidence_snippet,
                    evidence_field=rule.evidence_field,
                    explanation_text=rule.explanation_text,
                )
            )
        job.latest_bucket = decision.bucket
        job.latest_score = decision.final_score
        job.latest_decision_id = decision.id
        self.session.flush()
        return decision
