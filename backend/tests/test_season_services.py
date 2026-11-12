from datetime import date

import pytest

from app import create_app
from app.application.season.services import SeasonService
from app.domain.models.seasons import Season
from app.extensions import db


@pytest.fixture()
def season_service():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield SeasonService()
        db.session.remove()
        db.drop_all()


def create_season(service, *, name="Summer League 2026"):
    return service.create_season(
        name=name,
        year=2026,
        registration_start_date=date(2026, 4, 1),
        registration_end_date=date(2026, 4, 30),
        start_date=date(2026, 5, 1),
        end_date=date(2026, 8, 31),
    )


def test_create_season_persists_all_fields(season_service):
    season = create_season(season_service)

    assert season.id is not None
    assert season.name == "Summer League 2026"
    assert season.year == 2026
    assert season.registration_start_date == date(2026, 4, 1)
    assert season.registration_end_date == date(2026, 4, 30)
    assert season.start_date == date(2026, 5, 1)
    assert season.end_date == date(2026, 8, 31)
    assert season.season_status == "PLANNING"


def test_season_name_supports_documented_150_character_limit(season_service):
    name = "S" * 150

    season = create_season(season_service, name=name)

    assert season.name == name


def test_list_seasons_includes_history_ordered_by_year(season_service):
    old_season = create_season(season_service, name="Old League")
    season_service.transition_season(old_season.id, "REGISTRATION")
    season_service.transition_season(old_season.id, "ONGOING")
    season_service.transition_season(old_season.id, "COMPLETED")
    create_season(season_service, name="Current League")

    seasons = season_service.list_seasons()

    assert [season.name for season in seasons] == ["Current League", "Old League"]


def test_only_one_active_season_can_be_created(season_service):
    active_season = create_season(season_service, name="Active League")
    season_service.transition_season(active_season.id, "REGISTRATION")
    second_season = create_season(season_service, name="Second Active League")

    with pytest.raises(ValueError, match="Another season is already active"):
        season_service.transition_season(second_season.id, "REGISTRATION")


def test_completed_season_does_not_block_a_new_active_season(season_service):
    previous_season = create_season(season_service, name="Previous League")
    season_service.transition_season(previous_season.id, "REGISTRATION")
    season_service.transition_season(previous_season.id, "ONGOING")
    season_service.transition_season(previous_season.id, "COMPLETED")

    new_season = create_season(season_service, name="Next League")
    season_service.transition_season(new_season.id, "REGISTRATION")

    assert new_season.season_status == "REGISTRATION"
    assert Season.query.count() == 2


def test_duplicate_name_is_rejected(season_service):
    create_season(season_service)

    with pytest.raises(ValueError, match="already exists"):
        create_season(season_service)


def test_registration_window_must_be_ordered(season_service):
    with pytest.raises(ValueError, match="Registration start date"):
        season_service.create_season(
            name="Invalid Dates",
            year=2026,
            registration_start_date=date(2026, 5, 1),
            registration_end_date=date(2026, 4, 30),
        )


def test_registration_dates_may_be_omitted_together(season_service):
    season = season_service.create_season(name="No Registration Window", year=2026)

    assert season.registration_start_date is None
    assert season.registration_end_date is None


def test_status_transition_must_follow_lifecycle(season_service):
    season = create_season(season_service)

    with pytest.raises(ValueError, match="cannot transition from PLANNING to ONGOING"):
        season_service.transition_season(season.id, "ONGOING")