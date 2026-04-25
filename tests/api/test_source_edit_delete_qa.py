from __future__ import annotations


def create_source(client, *, name: str, base_slug: str, is_active: bool = True):
    response = client.post(
        "/sources",
        json={
            "name": name,
            "source_type": "greenhouse",
            "base_url": f"https://boards.greenhouse.io/{base_slug}",
            "external_identifier": base_slug,
            "company_name": name,
            "is_active": is_active,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_patch_rejects_duplicate_and_invalid_source_updates(client):
    original = create_source(client, name="Original Source", base_slug="original-source")
    conflict = create_source(client, name="Conflict Source", base_slug="conflict-source")

    duplicate_response = client.patch(
        f"/sources/{original['id']}",
        json={
            "base_url": conflict["base_url"],
            "external_identifier": conflict["external_identifier"],
        },
    )

    assert duplicate_response.status_code == 400
    duplicate_payload = duplicate_response.json()
    assert duplicate_payload["detail"]["message"] == "Source update failed."
    assert "Duplicate source already exists." in duplicate_payload["detail"]["errors"]["__all__"]

    invalid_response = client.patch(f"/sources/{original['id']}", json={"external_identifier": ""})

    assert invalid_response.status_code == 400
    invalid_payload = invalid_response.json()
    assert invalid_payload["detail"]["message"] == "Source update failed."
    assert "external_identifier" in invalid_payload["detail"]["errors"]

    detail_response = client.get(f"/sources/{original['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["source"]["base_url"] == "https://boards.greenhouse.io/original-source"
    assert detail_response.json()["source"]["external_identifier"] == "original-source"


def test_deleted_and_nonexistent_source_endpoints_return_not_found(client):
    source = create_source(client, name="Disposable Source", base_slug="disposable-source")

    delete_response = client.delete(f"/sources/{source['id']}")
    assert delete_response.status_code == 200

    for method_name, path in [
        ("patch", f"/sources/{source['id']}"),
        ("delete", f"/sources/{source['id']}"),
        ("get", f"/sources/{source['id']}/delete-impact"),
        ("post", f"/sources/{source['id']}/run"),
        ("get", f"/sources/{source['id']}"),
        ("patch", "/sources/999999"),
        ("delete", "/sources/999999"),
        ("get", "/sources/999999/delete-impact"),
        ("post", "/sources/999999/run"),
        ("get", "/sources/999999"),
    ]:
        method = getattr(client, method_name)
        kwargs = {"json": {"notes": "noop"}} if method_name == "patch" else {}
        response = method(path, **kwargs)
        assert response.status_code == 404
