from __future__ import annotations


def create_source(client, *, name: str, base_slug: str):
    response = client.post(
        "/sources",
        json={
            "name": name,
            "source_type": "greenhouse",
            "base_url": f"https://boards.greenhouse.io/{base_slug}",
            "external_identifier": base_slug,
            "company_name": name,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_sources_batch_run_controls_render_with_accessible_hooks(client):
    source = create_source(client, name="Batch Control Source", base_slug="batch-control-source")

    response = client.get("/sources", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert 'data-testid="source-batch-toolbar"' in response.text
    assert 'data-testid="run-all-button"' in response.text
    assert 'data-testid="run-selected-button"' in response.text
    assert 'data-testid="batch-confirmation-dialog"' in response.text
    assert 'data-source-batch-root' in response.text
    assert 'data-source-row-checkbox' in response.text
    assert f'aria-label="Select {source["name"]}"' in response.text
    assert 'role="dialog"' in response.text
    assert 'aria-modal="true"' in response.text


def test_sources_row_actions_are_compact_accessible_and_preserve_routes(client):
    source = create_source(client, name="Compact Action Source", base_slug="compact-action-source")

    response = client.get("/sources", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert f'href="/sources/{source["id"]}" aria-label="Open {source["name"]} source"' in response.text
    assert f'href="/sources/{source["id"]}/edit" aria-label="Edit {source["name"]} source"' in response.text
    assert f'action="/sources/{source["id"]}/run" data-requires-job-preferences-submit="true"' in response.text
    assert f'aria-label="Run {source["name"]} now"' in response.text
    assert f'href="/sources/{source["id"]}/delete" aria-label="Delete {source["name"]} source"' in response.text
    assert 'btn--danger' in response.text
