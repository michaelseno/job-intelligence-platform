from __future__ import annotations

from app.adapters.lever.adapter import LeverAdapter


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_lever_adapter_normalizes_jobs(monkeypatch):
    payload = [
        {
            "id": "abc",
            "text": "QA Automation Engineer",
            "hostedUrl": "https://jobs.example.com/qa",
            "categories": {"location": "Spain", "commitment": "Full-time"},
            "descriptionPlain": "QA automation role. Visa sponsorship available.",
            "createdAt": 1713866400000,
        }
    ]
    monkeypatch.setattr("app.adapters.lever.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(payload))
    source = type("Source", (), {"external_identifier": "example", "company_name": "Example", "name": "Example", "base_url": "https://example.com"})()

    result = LeverAdapter().fetch_jobs(source)

    assert len(result.jobs) == 1
    assert result.jobs[0].employment_type == "Full-time"
    assert result.jobs[0].location_text == "Spain"


def test_lever_adapter_tolerates_string_list_content(monkeypatch):
    payload = [
        {
            "id": "insider-1",
            "text": "Backend Engineer",
            "hostedUrl": "https://jobs.example.com/backend",
            "categories": {"location": "Remote", "commitment": "Full-time"},
            "descriptionPlain": "Core platform role.",
            "lists": [{"text": "Benefits", "content": "<p>Visa sponsorship available</p>"}],
            "additionalPlain": "Distributed team.",
            "createdAt": 1713866400000,
        }
    ]
    monkeypatch.setattr("app.adapters.lever.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(payload))
    source = type("Source", (), {"external_identifier": "insiderone", "company_name": "Insider", "name": "Insider", "base_url": "https://example.com"})()

    result = LeverAdapter().fetch_jobs(source)

    assert len(result.jobs) == 1
    assert "Visa sponsorship available" in result.jobs[0].description_text


def test_lever_adapter_tolerates_mixed_list_content(monkeypatch):
    payload = [
        {
            "id": "mixed-1",
            "text": "Data Engineer",
            "hostedUrl": "https://jobs.example.com/data",
            "categories": {},
            "lists": [
                {"content": [{"text": "Python"}, "SQL", {"unexpected": "ignored"}]},
                "unexpected group",
            ],
        }
    ]
    monkeypatch.setattr("app.adapters.lever.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(payload))
    source = type("Source", (), {"external_identifier": "example", "company_name": "Example", "name": "Example", "base_url": "https://example.com"})()

    result = LeverAdapter().fetch_jobs(source)

    assert len(result.jobs) == 1
    assert "Python" in result.jobs[0].description_text
    assert "SQL" in result.jobs[0].description_text
