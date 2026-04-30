from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


APP_JS = Path("app/static/js/app.js")


def parse_html(response):
    assert response.status_code == 200, response.text[:500]
    return BeautifulSoup(response.text, "html.parser")


def test_location_group_selector_shell_renders(client):
    soup = parse_html(client.get("/job-preferences", headers={"accept": "text/html"}))

    assert soup.find("input", id="location-search") is not None
    assert soup.find(id="location-clear") is not None
    assert soup.find(id="country-group") is not None
    assert soup.find(id="country-empty").get_text(strip=True) == "No countries or regions match your search."
    assert "aria-live" in soup.find(id="country-summary").attrs
    assert soup.find(id="country-legacy-warning") is not None


def test_static_country_data_preserves_required_regions_and_legacy_ids():
    source = APP_JS.read_text()

    for region in ["Europe", "Asia", "North America", "Australia / New Zealand", "Africa", "South America", "Middle East"]:
        assert f"label: '{region}'" in source

    for country_id in ["spain", "united_kingdom", "south_korea", "czech_republic", "hong_kong"]:
        assert f"['{country_id}'," in source

    for country_id in ["united_states", "canada", "mexico"]:
        assert f"['{country_id}'," in source
        assert f"['{country_id}'," in source and "'North America'" in source

    assert "selected_regions" not in source
    assert "[data-region-checkbox" in source
