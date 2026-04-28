from __future__ import annotations


CSV_HEADER = "name,source_type,base_url,external_identifier,adapter_key,company_name,is_active,notes\n"


def test_csv_source_import_normalizes_title_case_and_skips_duplicate_reupload(client):
    csv_body = (
        CSV_HEADER
        + "QA GH,Greenhouse,https://boards.greenhouse.io/qa-title,qa-title,,QA,true,normalized type\n"
        + "QA Lever,Lever,https://jobs.lever.co/qa-title,qa-title-lever,,QA,true,normalized type\n"
    )

    first_response = client.post("/sources/import", files={"file": ("sources.csv", csv_body, "text/csv")})

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["created"] == 2
    assert first_data["skipped_duplicate"] == 0
    assert first_data["invalid"] == 0
    assert [row["status"] for row in first_data["rows"]] == ["created", "created"]

    second_response = client.post("/sources/import", files={"file": ("sources.csv", csv_body, "text/csv")})

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["created"] == 0
    assert second_data["skipped_duplicate"] == 2
    assert second_data["invalid"] == 0
    assert [row["status"] for row in second_data["rows"]] == ["skipped_duplicate", "skipped_duplicate"]


def test_csv_source_import_reports_malformed_extra_fields_and_accepts_corrected_shape(client):
    malformed_csv = (
        CSV_HEADER
        + "Malformed,Greenhouse,https://boards.greenhouse.io/qa-malformed,qa-malformed,,QA,true,notes with comma,extra field\n"
    )

    malformed_response = client.post("/sources/import", files={"file": ("sources.csv", malformed_csv, "text/csv")})

    assert malformed_response.status_code == 200
    malformed_data = malformed_response.json()
    assert malformed_data["created"] == 0
    assert malformed_data["skipped_duplicate"] == 0
    assert malformed_data["invalid"] == 1
    assert malformed_data["rows"][0]["status"] == "invalid"
    assert "Quote values that contain commas" in malformed_data["rows"][0]["message"]

    corrected_csv = (
        CSV_HEADER
        + 'Corrected GH,Greenhouse,https://boards.greenhouse.io/qa-corrected,qa-corrected,,QA,true,"notes with comma, quoted"\n'
        + "Corrected Lever,Lever,https://jobs.lever.co/qa-corrected,qa-corrected-lever,,QA,true,valid lever row\n"
    )

    corrected_response = client.post("/sources/import", files={"file": ("job_board.csv", corrected_csv, "text/csv")})

    assert corrected_response.status_code == 200
    corrected_data = corrected_response.json()
    assert corrected_data["created"] == 2
    assert corrected_data["skipped_duplicate"] == 0
    assert corrected_data["invalid"] == 0
    assert [row["status"] for row in corrected_data["rows"]] == ["created", "created"]
