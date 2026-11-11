from datetime import date

import pytest

from app.application.season.policies import SeasonPolicy


def test_policy_normalizes_name_and_status():
    policy = SeasonPolicy()

    assert policy.normalize_name("  Summer League 2026  ") == "Summer League 2026"
    assert policy.normalize_status(" registration ") == "REGISTRATION"


def test_policy_rejects_season_start_before_registration_ends():
    policy = SeasonPolicy()

    with pytest.raises(ValueError, match="on or after registration ends"):
        policy.validate_season_details(
            year=2026,
            registration_start_date=date(2026, 4, 1),
            registration_end_date=date(2026, 4, 30),
            start_date=date(2026, 4, 29),
            end_date=date(2026, 8, 31),
        )


def test_policy_rejects_second_active_season():
    policy = SeasonPolicy()

    with pytest.raises(ValueError, match="Another season is already active"):
        policy.validate_active_season("ONGOING", has_active_season=True)


def test_policy_allows_historical_season_when_another_is_active():
    SeasonPolicy().validate_active_season("COMPLETED", has_active_season=True)