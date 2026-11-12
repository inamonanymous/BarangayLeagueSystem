from datetime import date

import pytest

from app import create_app
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.roles import Role
from app.domain.models.rosters import Roster
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


def season_payload(name="Summer League 2026", status="PLANNING"):
    return {
        "name": name,
        "year": 2026,
        "start_date": "2026-05-01",
        "end_date": "2026-08-31",
    }


def create_team_with_roster(
    season_id,
    *,
    name,
    minimum_roster_size,
    roster_size,
    archived_player_count=0,
    is_archived=False,
):
    sport = Sport(name=f"{name} Sport")
    division = Division(
        name=f"{name} Division",
        gender_policy="ANY",
        minimum_roster_size=minimum_roster_size,
        maximum_roster_size=max(minimum_roster_size, roster_size),
    )
    db.session.add_all([sport, division])
    db.session.flush()

    season_sport = SeasonSport(season_id=season_id, sport_id=sport.id)
    db.session.add(season_sport)
    db.session.flush()
    assignment = SeasonSportDivision(
        season_sport_id=season_sport.id,
        division_id=division.id,
    )
    db.session.add(assignment)
    db.session.flush()

    team = SeasonTeam(
        season_sport_division_id=assignment.id,
        name=name,
        barangay="Puting Kahoy",
        is_archived=is_archived,
    )
    db.session.add(team)
    db.session.flush()

    for index in range(roster_size):
        player = Player(
            first_name=f"{name} Player {index}",
            middle_name="",
            last_name="Test",
            birthdate=date(2000, 1, 1),
            gender="ANY",
            address="Puting Kahoy",
            is_archived=index < archived_player_count,
        )
        db.session.add(player)
        db.session.flush()
        db.session.add(
            Roster(
                season_team_id=team.id,
                player_id=player.id,
                jersey_number=str(index + 1),
            )
        )

    db.session.commit()
    return team


def test_season_history_is_public_and_includes_optional_dates(client):
    response = client.get("/api/v1/seasons/")

    assert response.status_code == 200
    assert response.get_json()["data"] == []


def test_admin_can_create_season(client):
    login(client)

    response = client.post("/api/v1/seasons/", json=season_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["name"] == "Summer League 2026"
    assert body["data"]["registration_start_date"] is None
    assert body["data"]["start_date"] == "2026-05-01"
    assert body["data"]["season_status"] == "PLANNING"
    assert Season.query.count() == 1


def test_non_admin_cannot_create_season(client):
    login(client, username="encoder", password="encoder-pass-123")

    response = client.post("/api/v1/seasons/", json=season_payload())

    assert response.status_code == 403


def test_anonymous_cannot_create_season(client):
    response = client.post("/api/v1/seasons/", json=season_payload())

    assert response.status_code == 401


def test_invalid_season_dates_return_bad_request(client):
    login(client)
    payload = season_payload()
    payload["registration_start_date"] = "2026-05-02"
    payload["registration_end_date"] = "2026-04-30"

    response = client.post("/api/v1/seasons/", json=payload)

    assert response.status_code == 400
    assert Season.query.count() == 0


def test_second_active_season_returns_conflict(client):
    login(client)
    first = client.post("/api/v1/seasons/", json=season_payload("First League"))
    second = client.post("/api/v1/seasons/", json=season_payload("Second League"))
    first_id = first.get_json()["data"]["id"]
    second_id = second.get_json()["data"]["id"]
    client.patch(
        f"/api/v1/seasons/{first_id}/status",
        json={"season_status": "REGISTRATION"},
    )

    response = client.patch(
        f"/api/v1/seasons/{second_id}/status",
        json={"season_status": "REGISTRATION"},
    )

    assert response.status_code == 409
    assert Season.query.count() == 2


def test_completed_seasons_remain_in_public_history(client):
    login(client)
    old_season = client.post("/api/v1/seasons/", json=season_payload("Old League"))
    client.post("/api/v1/seasons/", json=season_payload("New League"))
    old_id = old_season.get_json()["data"]["id"]
    for status in ("REGISTRATION", "ONGOING", "COMPLETED"):
        client.patch(
            f"/api/v1/seasons/{old_id}/status",
            json={"season_status": status},
        )

    response = client.get("/api/v1/seasons/")

    assert [item["name"] for item in response.get_json()["data"]] == ["New League", "Old League"]


def test_non_admin_cannot_transition_season(client):
    login(client)
    created = client.post("/api/v1/seasons/", json=season_payload())
    season_id = created.get_json()["data"]["id"]
    client.post("/api/v1/auth/logout")
    login(client, username="encoder", password="encoder-pass-123")

    response = client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "REGISTRATION"},
    )

    assert response.status_code == 403


def test_invalid_status_transition_returns_bad_request(client):
    login(client)
    created = client.post("/api/v1/seasons/", json=season_payload())
    season_id = created.get_json()["data"]["id"]

    response = client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "ONGOING"},
    )

    assert response.status_code == 400


def test_admin_can_advance_season_through_lifecycle(client):
    login(client)
    created = client.post("/api/v1/seasons/", json=season_payload())
    season_id = created.get_json()["data"]["id"]

    for status in ("REGISTRATION", "ONGOING", "COMPLETED", "ARCHIVED"):
        response = client.patch(
            f"/api/v1/seasons/{season_id}/status",
            json={"season_status": status},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["season_status"] == status


def test_season_cannot_move_to_ongoing_with_incomplete_roster(client):
    login(client)
    created = client.post("/api/v1/seasons/", json=season_payload())
    season_id = created.get_json()["data"]["id"]
    client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "REGISTRATION"},
    )
    create_team_with_roster(
        season_id,
        name="Falcons",
        minimum_roster_size=2,
        roster_size=2,
        archived_player_count=1,
    )

    response = client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "ONGOING"},
    )

    assert response.status_code == 409
    assert "Falcons (Falcons Division): 1/2 active players" in response.get_json()["message"]
    assert db.session.get(Season, season_id).season_status == "REGISTRATION"


def test_season_can_move_to_ongoing_when_active_teams_are_ready(client):
    login(client)
    created = client.post("/api/v1/seasons/", json=season_payload())
    season_id = created.get_json()["data"]["id"]
    client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "REGISTRATION"},
    )
    create_team_with_roster(
        season_id,
        name="Falcons",
        minimum_roster_size=2,
        roster_size=2,
    )
    create_team_with_roster(
        season_id,
        name="Archived Team",
        minimum_roster_size=5,
        roster_size=0,
        is_archived=True,
    )

    response = client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "ONGOING"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["season_status"] == "ONGOING"


def test_registration_window_requires_both_dates(client):
    login(client)
    payload = season_payload()
    payload["registration_start_date"] = "2026-04-01"

    response = client.post("/api/v1/seasons/", json=payload)

    assert response.status_code == 400