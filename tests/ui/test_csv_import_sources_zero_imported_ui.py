from __future__ import annotations

from io import BytesIO


CSV_HEADER = "name,source_type,base_url,external_identifier,adapter_key,company_name,is_active,notes\n"


def test_sources_import_ui_displays_created_skipped_invalid_counts_and_row_messages(client):
    initial_csv = CSV_HEADER + "UI GH,Greenhouse,https://boards.greenhouse.io/qa-ui,qa-ui,,QA,true,initial\n"
    initial_response = client.post(
        "/sources/import",
        headers={"accept": "text/html"},
        files={"file": ("sources.csv", BytesIO(initial_csv.encode("utf-8")), "text/csv")},
    )

    assert initial_response.status_code == 200
    assert "Import completed" in initial_response.text
    assert "Created" in initial_response.text
    assert "Skipped duplicates" in initial_response.text
    assert "Invalid rows" in initial_response.text
    assert "source created" in initial_response.text

    problem_csv = (
        CSV_HEADER
        + "UI GH Duplicate,Greenhouse,https://boards.greenhouse.io/qa-ui,qa-ui,,QA,true,duplicate\n"
        + "UI Bad,Greenhouse,https://boards.greenhouse.io/qa-ui-bad,qa-ui-bad,,QA,true,needs quoting,extra\n"
    )
    problem_response = client.post(
        "/sources/import",
        headers={"accept": "text/html"},
        files={"file": ("sources.csv", BytesIO(problem_csv.encode("utf-8")), "text/csv")},
    )

    assert problem_response.status_code == 200
    assert "Import completed with validation errors" in problem_response.text
    assert "No sources were imported. Review the invalid rows below" in problem_response.text
    assert "Skipped Duplicate" in problem_response.text
    assert "Invalid" in problem_response.text
    assert "Duplicate source already exists." in problem_response.text
    assert "Malformed CSV row: unexpected extra fields found. Quote values that contain commas." in problem_response.text
    assert "Imported 0 sources" not in problem_response.text
