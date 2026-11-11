from datetime import date, timedelta

import pytest

from app import create_app
from app.domain.models.divisions import Division
from app.domain.models.roles import Role
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.sports import Sport
from app.domain.models.users import User
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin_role = Role(name="Administrator", description="System administrator")
        encoder_role = Role(name="Encoder", description="Game encoder")
        db.session.add_all([admin_role, encoder_role])
        db.session.flush()
        admin = User(username="admin", role_id=admin_role.id, is_active=True)
        admin.set_password("admin-pass-123")
        encoder = User(username="encoder", role_id=encoder_role.id, is_active=True)
        encoder.set_password("encoder-pass-123")
        db.session.add_all([admin, encoder])
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def login(client, username="admin", password="admin-pass-123"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def create_division_assignment(client, *, status="REGISTRATION", window_start=None, window_end=None):
    today = date.today()
    start = window_start or today
    end = window_end or today
    season_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": f"Test Season {Season.query.count() + 1}",
            "year": today.year,
            "registration_start_date": start.isoformat(),
            "registration_end_date": end.isoformat(),
        },
    )
    assert season_response.status_code == 201
    season_id = season_response.get_json()["data"]["id"]
    if status == "REGISTRATION":
        transition = client.patch(
            f"/api/v1/seasons/{season_id}/status",
            json={"season_status": "REGISTRATION"},
        )
        assert transition.status_code == 200
    sport = Sport(name=f"Sport {season_id}")
    division = Division(
        name=f"Division {season_id}",
        gender_policy="ANY",
        minimum_roster_size=5,
        maximum_roster_size=15,
    )
    db.session.add_all([sport, division])
    db.session.flush()
    season_sport = SeasonSport(season_id=season_id, sport_id=sport.id)
    db.session.add(season_sport)
    db.session.flush()
    division_assignment = SeasonSportDivision(
        season_sport_id=season_sport.id,
        division_id=division.id,
    )
    db.session.add(division_assignment)
    db.session.commit()
    return season_id, division_assignment.id


def team_payload(name="Warriors"):
    return {
        "name": name,
        "barangay": "Puting Kahoy",
        "coach_name": "Coach A",
        "manager_name": "Manager B",
        "team_color": "Green",
    }


def test_list_teams_for_division(client):
    login(client)
    _, assignment_id = create_division_assignment(client)

    response = client.get(f"/api/v1/season-sport-divisions/{assignment_id}/teams")

    assert response.status_code == 200
    assert response.get_json()["data"] == []


def test_admin_can_register_team_during_registration_window(client):
    login(client)
    _, assignment_id = create_division_assignment(client)

    response = client.post(
        f"/api/v1/season-sport-divisions/{assignment_id}/teams",
        json=team_payload(),
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["name"] == "Warriors"
    assert SeasonTeam.query.one().barangay == "Puting Kahoy"


def test_non_admin_cannot_register_team(client):
    login(client)
    _, assignment_id = create_division_assignment(client)
    client.post("/api/v1/auth/logout")
    login(client, "encoder", "encoder-pass-123")

    response = client.post(
        f"/api/v1/season-sport-divisions/{assignment_id}/teams",
        json=team_payload(),
    )

    assert response.status_code == 403


def test_duplicate_team_name_in_division_returns_conflict(client):
    login(client)
    _, assignment_id = create_division_assignment(client)
    endpoint = f"/api/v1/season-sport-divisions/{assignment_id}/teams"
    client.post(endpoint, json=team_payload("Warriors"))

    response = client.post(endpoint, json=team_payload(" warriors "))

    assert response.status_code == 409
    assert SeasonTeam.query.count() == 1


def test_team_registration_requires_registration_status(client):
    login(client)
    _, assignment_id = create_division_assignment(client, status="PLANNING")

    response = client.post(
        f"/api/v1/season-sport-divisions/{assignment_id}/teams",
        json=team_payload(),
    )

    assert response.status_code == 400


def test_team_registration_must_be_within_configured_window(client):
    login(client)
    today = date.today()
    _, assignment_id = create_division_assignment(
        client,
        window_start=today - timedelta(days=4),
        window_end=today - timedelta(days=1),
    )

    response = client.post(
        f"/api/v1/season-sport-divisions/{assignment_id}/teams",
        json=team_payload(),
    )

    assert response.status_code == 400
    assert SeasonTeam.query.count() == 0


def test_division_assignment_with_team_cannot_be_removed(client):
    login(client)
    season_id, assignment_id = create_division_assignment(client)
    client.post(
        f"/api/v1/season-sport-divisions/{assignment_id}/teams",
        json=team_payload(),
    )
    division_assignment = db.session.get(SeasonSportDivision, assignment_id)
    season_sport_id = division_assignment.season_sport_id

    response = client.delete(
        f"/api/v1/seasons/sports/{season_sport_id}/divisions/{assignment_id}"
    )

    assert response.status_code == 409
    assert SeasonTeam.query.count() == 1
