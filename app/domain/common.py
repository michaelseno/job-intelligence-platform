from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def html_to_text(value: str | None) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    return clean_text(soup.get_text(" "))


def normalize_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value.strip())
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))


def slugify(value: str | None) -> str:
    cleaned = clean_text(value).lower()
    return re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()


def fingerprint(company: str | None, title: str, location: str | None, description: str | None) -> str:
    body = "|".join(
        [slugify(company), slugify(title), slugify(location), hashlib.sha1(clean_text(description)[:400].encode("utf-8")).hexdigest()[:12]]
    )
    return hashlib.sha1(body.encode("utf-8")).hexdigest()


def evidence_snippet(text: str | None, keyword: str, width: int = 140) -> str | None:
    source = clean_text(text)
    if not source:
        return None
    lower = source.lower()
    target = keyword.lower()
    idx = lower.find(target)
    if idx == -1:
        return None
    start = max(0, idx - width // 2)
    end = min(len(source), idx + len(keyword) + width // 2)
    snippet = source[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(source):
        snippet = snippet + "…"
    return snippet
