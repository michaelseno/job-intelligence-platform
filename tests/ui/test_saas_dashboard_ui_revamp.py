from fastapi.testclient import TestClient
import re

from app.main import app


client = TestClient(app, raise_server_exceptions=False)


def _assert_html_shell(response, expected_page_key: str, expected_title: str) -> None:
    assert response.status_code == 200, response.text[:500]
    assert response.headers["content-type"].startswith("text/html"), response.text[:500]
    body = response.text
    assert '<div class="app-shell"' in body
    assert f'data-page-key="{expected_page_key}"' in body
    assert expected_title in body
    assert 'href="http://testserver/static/css/app.css"' in body
    assert 'src="http://testserver/static/js/app.js"' in body


def test_dashboard_renders_html_shell() -> None:
    response = client.get("/dashboard")
    _assert_html_shell(response, "dashboard", "Operational dashboard")


def test_jobs_index_renders_management_table_ui() -> None:
    response = client.get("/jobs")
    _assert_html_shell(response, "jobs", "Job pipeline")
    assert 'Apply filters' in response.text
    assert 'Search title, company, or description' in response.text


def test_job_detail_renders_html_detail_view() -> None:
    response = client.get("/jobs/1")
    _assert_html_shell(response, "jobs", "Update tracking")


def test_sources_index_renders_management_table_ui() -> None:
    response = client.get("/sources")
    _assert_html_shell(response, "sources", "Source inventory")
    assert 'Add source' in response.text
    assert 'Import CSV' in response.text


def test_source_detail_renders_html_detail_view() -> None:
    source_index = client.get("/sources")
    match = re.search(r'/sources/(\d+)"', source_index.text)
    assert match, source_index.text[:1000]
    source_id = match.group(1)
    response = client.get(f"/sources/{source_id}")
    _assert_html_shell(response, "sources", "Recent runs")


def test_source_create_validation_uses_html_error_state() -> None:
    response = client.post(
        "/sources",
        data={"name": "", "source_type": "greenhouse", "base_url": ""},
    )
    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert 'Source update failed.' in response.text


def test_source_health_renders_in_shared_shell() -> None:
    response = client.get("/source-health")
    _assert_html_shell(response, "source_health", "Source health")
    assert 'Review source readiness' in response.text


def test_tracking_page_renders_in_shared_shell() -> None:
    response = client.get("/tracking")
    _assert_html_shell(response, "tracking", "Tracked jobs")
