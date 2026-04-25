from __future__ import annotations

from app.persistence.models import Source


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def create_source(client, *, name: str = "Editable Source", is_active: bool = True):
    response = client.post(
        "/sources",
        json={
            "name": name,
            "source_type": "greenhouse",
            "base_url": f"https://boards.greenhouse.io/{name.lower().replace(' ', '-')}",
            "external_identifier": name.lower().replace(" ", "-"),
            "company_name": "Example Co",
            "is_active": is_active,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_source_edit_html_flow_updates_values_and_shows_inactive_state(client):
    source = create_source(client)

    edit_page = client.get(f"/sources/{source['id']}/edit", headers={"accept": "text/html"})

    assert edit_page.status_code == 200
    assert "Edit source" in edit_page.text
    assert "Editable Source" in edit_page.text

    response = client.post(
        f"/sources/{source['id']}/edit",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={
            "name": "Edited Source",
            "source_type": "greenhouse",
            "company_name": "Updated Company",
            "base_url": "https://boards.greenhouse.io/edited-source",
            "external_identifier": "edited-source",
            "adapter_key": "",
            "notes": "Updated note",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/sources/{source['id']}?")

    detail_page = client.get(response.headers["location"], headers={"accept": "text/html"})
    assert detail_page.status_code == 200
    assert "Edited Source" in detail_page.text
    assert "Updated Company" in detail_page.text
    assert "Updated note" in detail_page.text
    assert "Inactive" in detail_page.text
    assert "cannot be run" in detail_page.text


def post_source_form(client, *, name: str, is_active_value=...):
    data = {
        "name": name,
        "source_type": "greenhouse",
        "company_name": "Checkbox Co",
        "base_url": f"https://boards.greenhouse.io/{name.lower().replace(' ', '-')}",
        "external_identifier": name.lower().replace(" ", "-"),
        "adapter_key": "",
        "notes": "",
    }
    if is_active_value is not ...:
        data["is_active"] = is_active_value
    return client.post(
        "/sources",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data=data,
        follow_redirects=False,
    )


def test_source_create_form_accepts_true_checkbox_value(client, session):
    response = post_source_form(client, name="True Active Source", is_active_value="true")

    assert response.status_code == 303
    source = session.query(Source).filter_by(name="True Active Source").one()
    assert source.is_active is True


def test_source_create_form_accepts_on_checkbox_value(client, session):
    response = post_source_form(client, name="On Active Source", is_active_value="on")

    assert response.status_code == 303
    source = session.query(Source).filter_by(name="On Active Source").one()
    assert source.is_active is True


def test_source_create_form_omitted_checkbox_persists_inactive(client, session):
    response = post_source_form(client, name="Omitted Inactive Source")

    assert response.status_code == 303
    source = session.query(Source).filter_by(name="Omitted Inactive Source").one()
    assert source.is_active is False


def test_source_edit_form_accepts_true_checkbox_value(client, session):
    source = create_source(client, name="Edit True Source", is_active=False)

    response = client.post(
        f"/sources/{source['id']}/edit",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={
            "name": "Edit True Source",
            "source_type": "greenhouse",
            "company_name": "Checkbox Co",
            "base_url": "https://boards.greenhouse.io/edit-true-source",
            "external_identifier": "edit-true-source",
            "adapter_key": "",
            "notes": "Updated active state",
            "is_active": "true",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    session.expire_all()
    assert session.get(Source, source["id"]).is_active is True


def test_source_created_with_true_checkbox_can_run_without_inactive_conflict(client, session, monkeypatch):
    monkeypatch.setattr("app.adapters.greenhouse.adapter.httpx.get", lambda *args, **kwargs: DummyResponse({"jobs": []}))
    create_response = post_source_form(client, name="Runnable True Source", is_active_value="true")
    assert create_response.status_code == 303
    source = session.query(Source).filter_by(name="Runnable True Source").one()

    run_response = client.post(f"/sources/{source.id}/run?next=/sources")

    assert run_response.status_code == 200
    assert run_response.json()["source_id"] == source.id


def test_source_delete_html_flow_hides_deleted_source_from_management_surfaces(client):
    source = create_source(client, name="Delete Me")

    delete_page = client.get(f"/sources/{source['id']}/delete", headers={"accept": "text/html"})

    assert delete_page.status_code == 200
    assert "Delete source" in delete_page.text
    assert "No run history found." in delete_page.text
    assert "No linked jobs found." in delete_page.text

    response = client.post(
        f"/sources/{source['id']}/delete",
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "text/html"},
        data={},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/sources?")

    sources_page = client.get(response.headers["location"], headers={"accept": "text/html"})
    assert sources_page.status_code == 200
    assert "Delete Me" not in sources_page.text

    detail_response = client.get(f"/sources/{source['id']}", headers={"accept": "text/html"})
    assert detail_response.status_code == 404

    jobs_page = client.get("/jobs", headers={"accept": "text/html"})
    assert jobs_page.status_code == 200
    assert "Delete Me" not in jobs_page.text
