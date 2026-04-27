from __future__ import annotations

from bs4 import BeautifulSoup

from app.persistence.models import Source


def parse_html(response):
    assert response.status_code == 200, response.text[:500]
    assert response.headers["content-type"].startswith("text/html")
    return BeautifulSoup(response.text, "html.parser")


def test_primary_nav_places_job_preferences_between_dashboard_and_jobs(client):
    soup = parse_html(client.get("/job-preferences", headers={"accept": "text/html"}))
    labels = [link.get_text(strip=True) for link in soup.select("nav.sidebar__nav a.nav-link")]

    assert labels[:3] == ["Dashboard", "Job Preferences", "Jobs"]
    preferences_link = soup.select_one('nav.sidebar__nav a[href="/job-preferences"]')
    assert preferences_link is not None
    assert "is-active" in preferences_link.get("class", [])


def test_job_preferences_page_renders_wizard_steps_and_hides_advanced_setup(client):
    soup = parse_html(client.get("/job-preferences?next=/jobs", headers={"accept": "text/html"}))

    assert soup.find("h1", string="Job Preferences") is not None
    root = soup.find(id="job-preferences-root")
    assert root is not None
    assert root["data-next"] == "/jobs"

    assert soup.find(id="job-preferences-page-title").get_text(strip=True) == "Set up Job Preferences"
    progress = [item.get_text(strip=True) for item in soup.select("#job-preferences-progress li")]
    assert progress == [
        "Step 1 of 4: Job categories",
        "Step 2 of 4: Location",
        "Step 3 of 4: Work arrangement",
        "Step 4 of 4: Visa sponsorship",
    ]
    assert soup.find("input", id="category-search") is not None
    assert soup.find(id="category-group") is not None
    assert soup.find(id="country-group") is not None
    assert soup.find(id="work-arrangement-group") is not None
    assert soup.find(id="visa-group") is not None
    assert soup.find(id="advanced-settings") is not None
    assert "hidden" in soup.find(id="advanced-settings").get("class", [])

    save_button = soup.find("button", id="job-preferences-save")
    assert save_button is not None
    assert save_button.get_text(strip=True) == "Save preferences"


def test_job_preferences_wizard_contains_approved_options_only(client):
    soup = parse_html(client.get("/job-preferences", headers={"accept": "text/html"}))
    text = soup.get_text(" ")

    for label in ["Remote", "Hybrid", "On-site", "Flexible / Any", "I require visa sponsorship"]:
        assert label in text

    # Options are rendered by JavaScript from the approved catalogs; no add-custom affordance is present.
    assert "Add custom category" not in text
    assert "Custom category" not in text


def test_job_preferences_page_excludes_out_of_scope_runtime_or_weight_fields(client):
    soup = parse_html(client.get("/job-preferences", headers={"accept": "text/html"}))
    form = soup.find("form", id="job-preferences-form")
    text = form.get_text(" ").lower()
    field_names = {field.get("name", "") for field in form.find_all(["input", "textarea", "select"])}

    assert not {"bucket", "tracking_status", "source", "search", "sort"} & field_names
    for forbidden in ["salary", "job type", "experience level", "custom weights", "thresholds", "dynamodb", "authentication"]:
        assert forbidden not in text


def test_source_run_forms_are_marked_for_preference_injection(client, session):
    source = Source(
        name="Preference Injection Source",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/preference-injection",
        external_identifier="preference-injection",
        dedupe_key="preference-injection",
        is_active=True,
    )
    session.add(source)
    session.commit()

    for path in ["/sources", f"/sources/{source.id}"]:
        soup = parse_html(client.get(path, headers={"accept": "text/html"}))
        form = soup.find("form", attrs={"action": f"/sources/{source.id}/run"})
        assert form is not None
        assert form.get("data-requires-job-preferences-submit") == "true"
        assert form.find("input", attrs={"name": "next"}) is not None


def test_preference_dependent_pages_are_client_guarded(client):
    for path, key in [("/dashboard", "dashboard"), ("/jobs", "jobs"), ("/digest/latest", "digest"), ("/reminders", "reminders")]:
        soup = parse_html(client.get(path, headers={"accept": "text/html"}))
        shell = soup.select_one(".app-shell")
        assert shell["data-page-key"] == key
        assert shell["data-requires-job-preferences"] == "true"
