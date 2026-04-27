from __future__ import annotations

import pytest

from app.domain.job_preferences import JobFilterPreferencesError, validate_job_filter_preferences


def test_validator_trims_drops_blanks_and_deduplicates_case_insensitively():
    preferences = validate_job_filter_preferences(
        {
            "schema_version": 1,
            "role_positives": {" platform qa ": [" Test Platform ", "test platform", ""]},
            "role_negatives": [" Sales ", "sales", ""],
            "remote_positives": [" Remote ", "remote"],
            "location_positives": [" Lisbon ", ""],
            "location_negatives": [],
            "sponsorship_supported": [],
            "sponsorship_unsupported": [],
            "sponsorship_ambiguous": [],
        }
    )

    assert preferences.role_positives == {"platform qa": ["Test Platform"]}
    assert preferences.role_negatives == ["Sales"]
    assert preferences.remote_positives == ["Remote"]
    assert preferences.location_positives == ["Lisbon"]


def test_validator_preserves_same_keyword_across_separate_role_families():
    preferences = validate_job_filter_preferences(
        {
            "schema_version": 1,
            "role_positives": {"family one": ["shared keyword"], "family two": ["shared keyword"]},
            "role_negatives": [],
            "remote_positives": [],
            "location_positives": [],
            "location_negatives": [],
            "sponsorship_supported": [],
            "sponsorship_unsupported": [],
            "sponsorship_ambiguous": [],
        }
    )

    assert preferences.role_positives["family one"] == ["shared keyword"]
    assert preferences.role_positives["family two"] == ["shared keyword"]


def test_validator_rejects_missing_positive_signals():
    with pytest.raises(JobFilterPreferencesError) as excinfo:
        validate_job_filter_preferences(
            {
                "schema_version": 1,
                "role_positives": {"empty": []},
                "role_negatives": [],
                "remote_positives": [],
                "location_positives": [],
                "location_negatives": [],
                "sponsorship_supported": [],
                "sponsorship_unsupported": [],
                "sponsorship_ambiguous": [],
            }
        )

    assert "__all__" in excinfo.value.errors


def test_validator_rejects_unsupported_schema_version():
    with pytest.raises(JobFilterPreferencesError) as excinfo:
        validate_job_filter_preferences({"schema_version": 2, "role_positives": {"backend": ["backend"]}})

    assert "schema_version" in excinfo.value.errors
