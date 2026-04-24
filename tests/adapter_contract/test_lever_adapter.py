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
