from datetime import date

import pytest

from app import create_app
from app.domain.models.divisions import Division
from app.domain.models.players import Player
from app.domain.models.roles import Role
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
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
        db.session.add(admin_role)
        db.session.flush()
        admin = User(username="admin", role_id=admin_role.id, is_active=True)
        admin.set_password("admin-pass-123")
        db.session.add(admin)
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def login(client):
    return client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass-123"})


def create_registration_team(client):
    today = date.today()
    season_response = client.post(
        "/api/v1/seasons/",
        json={
            "name": "Roster Season",
            "year": today.year,
            "registration_start_date": today.isoformat(),
            "registration_end_date": today.isoformat(),
        },
    )
    season_id = season_response.get_json()["data"]["id"]
    client.patch(
        f"/api/v1/seasons/{season_id}/status",
        json={"season_status": "REGISTRATION"},
    )
    sport = Sport(name="Basketball")
    division = Division(
        name="Senior",
        gender_policy="ANY",
        minimum_roster_size=5,
        maximum_roster_size=12,
    )
    db.session.add_all([sport, division])
    db.session.flush()
    season_sport = SeasonSport(season_id=season_id, sport_id=sport.id)
    db.session.add(season_sport)
    db.session.flush()
    assignment = SeasonSportDivision(season_sport_id=season_sport.id, division_id=division.id)
    db.session.add(assignment)
    db.session.flush()
    team = SeasonTeam(
        season_sport_division_id=assignment.id,
        name="Warriors",
        barangay="Puting Kahoy",
    )
    db.session.add(team)
    db.session.commit()
    return season_id, assignment.id, team.id


def player_payload(first_name="Alex", last_name="Rivera", birthdate="2010-03-10"):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "birthdate": birthdate,
        "gender": "MALE",
        "address": "Puting Kahoy",
    }


def test_player_crud_uses_soft_archive_and_restore(client):
    login(client)
    created = client.post("/api/v1/players/", json=player_payload())
    assert created.status_code == 201
    player_id = created.get_json()["data"]["id"]

    updated = client.put(
        f"/api/v1/players/{player_id}",
        json=player_payload(first_name="Alexis"),
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["first_name"] == "Alexis"

    archived = client.delete(f"/api/v1/players/{player_id}")
    assert archived.status_code == 200
    assert archived.get_json()["data"]["is_archived"] is True
    assert client.get("/api/v1/players/").get_json()["data"] == []

    restored = client.patch(
        f"/api/v1/players/{player_id}/archive",
        json={"is_archived": False},
    )
    assert restored.status_code == 200
    assert restored.get_json()["data"]["is_archived"] is False
    assert Player.query.count() == 1


def test_duplicate_player_identity_is_rejected(client):
    login(client)
    client.post("/api/v1/players/", json=player_payload())

    response = client.post("/api/v1/players/", json=player_payload(first_name=" alex "))

    assert response.status_code == 409
    assert Player.query.count() == 1


def test_team_can_be_updated_and_archived(client):
    login(client)
    _, _, team_id = create_registration_team(client)

    updated = client.put(
        f"/api/v1/season-teams/{team_id}",
        json={"name": "Updated Warriors", "barangay": "Central", "team_color": "Blue"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["name"] == "Updated Warriors"

    archived = client.delete(f"/api/v1/season-teams/{team_id}")
    assert archived.status_code == 200
    assert archived.get_json()["data"]["is_archived"] is True


def test_roster_crud_unlinks_player_without_deleting_profile(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    player = client.post("/api/v1/players/", json=player_payload()).get_json()["data"]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"

    added = client.post(
        roster_url,
        json={"player_id": player["id"], "jersey_number": "7"},
    )
    assert added.status_code == 201
    roster_id = added.get_json()["data"]["id"]
    assert client.get(roster_url).get_json()["data"][0]["player"]["id"] == player["id"]

    updated = client.put(
        f"{roster_url}/{roster_id}",
        json={"jersey_number": "11"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["jersey_number"] == "11"

    removed = client.delete(f"{roster_url}/{roster_id}")
    assert removed.status_code == 200
    assert Roster.query.count() == 0
    assert Player.query.filter_by(id=player["id"]).one().is_archived is False


def test_archived_team_rejects_roster_updates_and_removals(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    player = client.post("/api/v1/players/", json=player_payload()).get_json()["data"]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"
    added = client.post(
        roster_url,
        json={"player_id": player["id"], "jersey_number": "7"},
    )
    roster_id = added.get_json()["data"]["id"]
    archived = client.delete(f"/api/v1/season-teams/{team_id}")
    assert archived.status_code == 200

    updated = client.put(
        f"{roster_url}/{roster_id}",
        json={"jersey_number": "11"},
    )
    removed = client.delete(f"{roster_url}/{roster_id}")

    assert updated.status_code == 400
    assert removed.status_code == 400
    assert Roster.query.count() == 1


def test_adult_roster_player_requires_voter_verification(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"

    rejected = client.post(roster_url, json={"player_id": adult["id"], "jersey_number": "8"})
    assert rejected.status_code == 400

    accepted = client.post(
        roster_url,
        json={
            "player_id": adult["id"],
            "jersey_number": "8",
            "voter_verified": True,
            "voter_number": "VOTER-123",
        },
    )
    assert accepted.status_code == 201
    eligibility = SeasonPlayerEligibility.query.one()
    assert eligibility.is_voter_verified is True
    assert eligibility.voter_number == "VOTER-123"


def test_roster_enforces_jersey_uniqueness_and_roster_max(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    division = Division.query.one()
    division.maximum_roster_size = 1
    db.session.commit()
    first = client.post("/api/v1/players/", json=player_payload()).get_json()["data"]
    second = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Jamie"),
    ).get_json()["data"]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"
    client.post(roster_url, json={"player_id": first["id"], "jersey_number": "3"})

    same_jersey = client.post(roster_url, json={"player_id": second["id"], "jersey_number": "3"})

    assert same_jersey.status_code == 409
    assert Roster.query.count() == 1
