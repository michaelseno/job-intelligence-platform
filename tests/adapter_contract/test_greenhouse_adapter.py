from __future__ import annotations

from app.adapters.greenhouse.adapter import GreenhouseAdapter


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_greenhouse_adapter_normalizes_jobs(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 1,
                "title": "Python Backend Engineer",
                "absolute_url": "https://example.com/jobs/1",
                "location": {"name": "Remote"},
                "content": "<p>Python backend role with sponsorship available.</p>",
                "updated_at": "2026-04-23T10:00:00Z",
            }
        ]
    }
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse(payload))
    source = type("Source", (), {"external_identifier": "example", "company_name": "Example", "name": "Example", "base_url": "https://example.com"})()

    result = GreenhouseAdapter().fetch_jobs(source)

    assert len(result.jobs) == 1
    assert result.jobs[0].title == "Python Backend Engineer"
    assert "sponsorship available" in result.jobs[0].description_text.lower()
