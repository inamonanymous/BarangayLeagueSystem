from datetime import date, timedelta

import pytest

from app import create_app
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.roles import Role
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.users import User
from app.extensions import db
from seed_demo_teams import SEASON_NAME, seed_demo_teams, verify_demo_teams


@pytest.fixture()
def demo_database():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        role = Role(name="Administrator")
        db.session.add(role)
        db.session.flush()
        admin = User(username="admin", role_id=role.id, is_active=True)
        admin.set_password("test-password")
        today = date.today()
        season = Season(
            name=SEASON_NAME,
            year=today.year,
            season_status="REGISTRATION",
            registration_start_date=today,
            registration_end_date=today,
        )
        db.session.add_all([
            admin,
            season,
            Division(name="Senior", gender_policy="ANY", minimum_roster_size=10, maximum_roster_size=15),
            Division(name="Junior", gender_policy="ANY", minimum_roster_size=10, maximum_roster_size=15),
        ])
        db.session.commit()
        yield admin, season
        db.session.remove()
        db.drop_all()


def test_seed_creates_complete_rosters_and_is_repeatable(demo_database):
    admin, season = demo_database
    seed_demo_teams(admin.id)
    seed_demo_teams(admin.id)

    assert Player.query.count() == 70
    assert Roster.query.count() == 70
    assert SeasonPlayerEligibility.query.filter_by(season_id=season.id).count() == 40
    for division in Division.query.all():
        assignment = SeasonSportDivision.query.filter_by(division_id=division.id).one()
        teams = SeasonTeam.query.filter_by(season_sport_division_id=assignment.id).all()
        assert len(teams) >= 3
        assert all(Roster.query.filter_by(season_team_id=team.id).count() == 10 for team in teams)
    eligibility = SeasonPlayerEligibility.query.first()
    assert eligibility.verified_by == admin.id
    assert eligibility.voter_number.startswith("DEMO-")
    assert "not real" in eligibility.notes


def test_seed_rejects_closed_registration_before_creating_data(demo_database):
    admin, season = demo_database
    season.registration_end_date = date.today() - timedelta(days=1)
    season.registration_start_date = season.registration_end_date
    db.session.commit()

    with pytest.raises(ValueError, match="outside the season registration window"):
        seed_demo_teams(admin.id)

    assert SeasonTeam.query.count() == 0
    assert Player.query.count() == 0


def test_read_only_check_reports_other_incomplete_teams(demo_database, capsys):
    admin, season = demo_database
    seed_demo_teams(admin.id)
    assignment = SeasonSportDivision.query.join(Division).filter(Division.name == "Senior").one()
    db.session.add(SeasonTeam(
        season_sport_division_id=assignment.id, name="Existing Team", barangay="Existing"
    ))
    season.season_status = "ONGOING"
    db.session.commit()
    counts_before = (SeasonTeam.query.count(), Player.query.count(), Roster.query.count())
    capsys.readouterr()

    verify_demo_teams()

    output = capsys.readouterr().out
    assert "VERIFIED: all sample teams and players are present." in output
    assert "SEASON NOT READY: Senior / Existing Team: 0/10 active players" in output
    assert (SeasonTeam.query.count(), Player.query.count(), Roster.query.count()) == counts_before


def test_check_rejects_missing_roster_and_altered_voter_details(demo_database):
    admin, _ = demo_database
    seed_demo_teams(admin.id)
    roster = Roster.query.first()
    eligibility = SeasonPlayerEligibility.query.filter_by(player_id=roster.player_id).one()
    eligibility.voter_number = "changed"
    db.session.delete(roster)
    another_eligibility = SeasonPlayerEligibility.query.filter(
        SeasonPlayerEligibility.id != eligibility.id
    ).first()
    another_eligibility.is_voter_verified = False
    db.session.commit()
    count_before = Roster.query.count()

    with pytest.raises(ValueError) as error:
        verify_demo_teams()

    assert "not on this roster" in str(error.value)
    assert "fictional voter verification is missing or changed" in str(error.value)
    assert Roster.query.count() == count_before

    with pytest.raises(ValueError, match="has changed voter details"):
        seed_demo_teams(admin.id)
    assert eligibility.voter_number == "changed"
    assert Roster.query.count() == count_before
