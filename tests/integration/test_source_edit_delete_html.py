from __future__ import annotations


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
