from datetime import date

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.application.rosters.policies import RosterPolicy
from app.application.rosters.services import RosterService
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
from app.infrastructure.database.roster_repository import RosterRepository


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
    added_data = added.get_json()["data"]
    roster_id = added_data["id"]
    assert added_data == db.session.get(Roster, roster_id).to_dict()
    assert client.get(roster_url).get_json()["data"] == [{**added_data, "player": player}]

    updated = client.put(
        f"{roster_url}/{roster_id}",
        json={"jersey_number": "11"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["jersey_number"] == "11"
    assert updated.get_json()["data"] == db.session.get(Roster, roster_id).to_dict()

    removed = client.delete(f"{roster_url}/{roster_id}")
    assert removed.status_code == 200
    assert Roster.query.count() == 0
    assert Player.query.filter_by(id=player["id"]).one().is_archived is False


def test_roster_edit_and_remove_preserve_validation_and_ordering(client):
    login(client)
    season_id, assignment_id, team_id = create_registration_team(client)
    other_team = SeasonTeam(name="Other", barangay="Central", season_sport_division_id=assignment_id)
    db.session.add(other_team)
    db.session.commit()
    players = [
        client.post("/api/v1/players/", json=player_payload(first_name=name)).get_json()["data"]
        for name in ("First", "Second")
    ]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"
    first = client.post(roster_url, json={"player_id": players[0]["id"], "jersey_number": "7"}).get_json()["data"]
    second = client.post(roster_url, json={"player_id": players[1]["id"], "jersey_number": "11"}).get_json()["data"]
    assert [entry["id"] for entry in client.get(roster_url).get_json()["data"]] == [second["id"], first["id"]]
    assert client.put(f"{roster_url}/{first['id']}", json={"jersey_number": "11"}).status_code == 409
    wrong_team_url = f"/api/v1/season-teams/{other_team.id}/roster/{first['id']}"
    assert client.put(wrong_team_url, json={"jersey_number": "12"}).status_code == 404
    assert client.delete(wrong_team_url).status_code == 404
    season = db.session.get(Season, season_id)
    season.season_status = "ONGOING"
    db.session.commit()
    assert client.put(f"{roster_url}/{first['id']}", json={"jersey_number": "12"}).status_code == 400
    assert client.delete(f"{roster_url}/{first['id']}").status_code == 400
    assert Roster.query.count() == 2


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


@pytest.mark.parametrize("existing_eligibility", [False, True])
def test_roster_and_adult_eligibility_roll_back_together_on_conflict(client, monkeypatch, existing_eligibility):
    login(client)
    season_id, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    if existing_eligibility:
        db.session.add(SeasonPlayerEligibility(
            season_id=season_id, player_id=adult["id"], is_voter_verified=False,
            voter_number="OLD", notes="Keep this note",
        ))
        db.session.commit()

    original_add = RosterRepository.add_roster

    def fail_after_flush(repository, team_id, player_id, jersey_number):
        original_add(repository, team_id, player_id, jersey_number)
        raise IntegrityError("insert roster", {}, Exception("simulated conflict"))

    monkeypatch.setattr(RosterRepository, "add_roster", fail_after_flush)
    response = client.post(
        f"/api/v1/season-teams/{team_id}/roster",
        json={
            "player_id": adult["id"], "jersey_number": "8",
            "voter_verified": True, "voter_number": "NEW", "eligibility_notes": "New note",
        },
    )
    assert response.status_code == 409
    assert Roster.query.count() == 0
    eligibility = SeasonPlayerEligibility.query.filter_by(season_id=season_id, player_id=adult["id"]).first()
    if existing_eligibility:
        assert eligibility is not None
        assert eligibility.is_voter_verified is False
        assert eligibility.voter_number == "OLD"
        assert eligibility.notes == "Keep this note"
    else:
        assert eligibility is None


def test_roster_rolls_back_unexpected_write_errors(client, monkeypatch):
    login(client)
    _, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    original_add = RosterRepository.add_roster

    def fail_after_flush(repository, team_id, player_id, jersey_number):
        original_add(repository, team_id, player_id, jersey_number)
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(RosterRepository, "add_roster", fail_after_flush)
    admin_id = User.query.filter_by(username="admin").one().id
    with pytest.raises(RuntimeError, match="unexpected failure"):
        RosterService().add_player(
            team_id, player_id=adult["id"], jersey_number="8", actor_id=admin_id,
            voter_verified=True, voter_number="NEW",
        )
    assert Roster.query.count() == 0
    assert SeasonPlayerEligibility.query.count() == 0


def test_roster_and_eligibility_roll_back_when_commit_fails(client, monkeypatch):
    login(client)
    _, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    admin_id = User.query.filter_by(username="admin").one().id

    def fail_commit():
        raise IntegrityError("commit", {}, Exception("simulated commit conflict"))

    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", fail_commit)
        with pytest.raises(ValueError, match="Roster player or jersey number conflicts"):
            RosterService().add_player(
                team_id, player_id=adult["id"], jersey_number="8", actor_id=admin_id,
                voter_verified=True, voter_number="NEW",
            )
    assert Roster.query.count() == 0
    assert SeasonPlayerEligibility.query.count() == 0


def test_adult_roster_add_commits_both_writes_once(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    admin_id = User.query.filter_by(username="admin").one().id
    commits = []

    def record_commit(session):
        commits.append(session)

    session = db.session()
    event.listen(session, "after_commit", record_commit)
    try:
        RosterService().add_player(
            team_id, player_id=adult["id"], jersey_number="8", actor_id=admin_id,
            voter_verified=True, voter_number="NEW",
        )
    finally:
        event.remove(session, "after_commit", record_commit)
    assert len(commits) == 1
    assert Roster.query.count() == 1
    assert SeasonPlayerEligibility.query.count() == 1


def test_adult_verification_is_required_again_after_removal(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    roster_url = f"/api/v1/season-teams/{team_id}/roster"
    payload = {
        "player_id": adult["id"], "jersey_number": "8",
        "voter_verified": True, "voter_number": "  VOTER-123  ",
    }
    added = client.post(roster_url, json=payload)
    assert added.status_code == 201
    assert SeasonPlayerEligibility.query.one().voter_number == "VOTER-123"
    assert client.delete(f"{roster_url}/{added.get_json()['data']['id']}").status_code == 200

    rejected = client.post(roster_url, json={"player_id": adult["id"], "jersey_number": "8"})
    assert rejected.status_code == 400
    assert Roster.query.count() == 0
    assert client.post(roster_url, json=payload).status_code == 201
    assert SeasonPlayerEligibility.query.count() == 1


def test_adult_reverification_preserves_existing_notes_when_blank(client):
    login(client)
    season_id, _, team_id = create_registration_team(client)
    adult = client.post(
        "/api/v1/players/",
        json=player_payload(first_name="Adult", birthdate="1990-01-01"),
    ).get_json()["data"]
    db.session.add(SeasonPlayerEligibility(
        season_id=season_id, player_id=adult["id"], is_voter_verified=False,
        voter_number="OLD", notes="Keep this note",
    ))
    db.session.commit()
    response = client.post(
        f"/api/v1/season-teams/{team_id}/roster",
        json={
            "player_id": adult["id"], "jersey_number": "8", "voter_verified": True,
            "voter_number": "  NEW  ", "eligibility_notes": "   ",
        },
    )
    assert response.status_code == 201
    eligibility = SeasonPlayerEligibility.query.one()
    assert eligibility.voter_number == "NEW"
    assert eligibility.is_voter_verified is True
    assert eligibility.verified_by == User.query.filter_by(username="admin").one().id
    assert eligibility.verified_at is not None
    assert eligibility.notes == "Keep this note"


@pytest.mark.parametrize(
    ("today", "expected"),
    [(date(2026, 3, 9), False), (date(2026, 3, 10), True)],
)
def test_voter_requirement_starts_on_eighteenth_birthday(today, expected):
    policy = RosterPolicy()
    birthdate = date(2008, 3, 10)
    if expected:
        with pytest.raises(ValueError, match="voter-verified"):
            policy.validate_voter_details(birthdate, today, False, None)
    else:
        assert policy.validate_voter_details(birthdate, today, False, None) is None


def test_roster_add_rejects_missing_archived_and_duplicate_players(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    roster_url = f"/api/v1/season-teams/{team_id}/roster"
    player = client.post("/api/v1/players/", json=player_payload()).get_json()["data"]
    payload = {"player_id": player["id"], "jersey_number": "7"}

    missing = client.post(roster_url, json={"player_id": 99999, "jersey_number": "7"})
    assert missing.status_code == 404
    assert client.delete(f"/api/v1/players/{player['id']}").status_code == 200
    archived = client.post(roster_url, json=payload)
    assert archived.status_code == 404
    assert client.patch(f"/api/v1/players/{player['id']}/archive", json={"is_archived": False}).status_code == 200
    assert client.post(roster_url, json=payload).status_code == 201
    duplicate = client.post(roster_url, json=payload)
    assert duplicate.status_code == 409
    assert duplicate.get_json()["message"] == "This player is already on the team roster."
    assert Roster.query.count() == 1


def test_roster_add_rejects_missing_or_archived_team(client):
    login(client)
    _, _, team_id = create_registration_team(client)
    player = client.post("/api/v1/players/", json=player_payload()).get_json()["data"]
    payload = {"player_id": player["id"], "jersey_number": "7"}

    assert client.post("/api/v1/season-teams/99999/roster", json=payload).status_code == 404
    assert client.delete(f"/api/v1/season-teams/{team_id}").status_code == 200
    assert client.post(f"/api/v1/season-teams/{team_id}/roster", json=payload).status_code == 400
    assert Roster.query.count() == 0


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
    over_capacity = client.post(roster_url, json={"player_id": second["id"], "jersey_number": "4"})
    assert over_capacity.status_code == 400
    assert Roster.query.count() == 1


def test_available_players_follow_sport_season_and_team_archive_rules(client):
    login(client)
    season_id, assignment_id, team_id = create_registration_team(client)
    assignment = db.session.get(SeasonSportDivision, assignment_id)
    original_sport = db.session.get(SeasonSport, assignment.season_sport_id)
    junior = Division(name="Junior", gender_policy="ANY", minimum_roster_size=5, maximum_roster_size=12)
    volleyball = Sport(name="Volleyball")
    other_season = Season(name="Other season", year=date.today().year, season_status="PLANNING")
    db.session.add_all([junior, volleyball, other_season])
    db.session.flush()
    volleyball_association = SeasonSport(season_id=season_id, sport_id=volleyball.id)
    other_association = SeasonSport(season_id=other_season.id, sport_id=original_sport.sport_id)
    db.session.add_all([volleyball_association, other_association])
    db.session.flush()
    junior_assignment = SeasonSportDivision(season_sport_id=original_sport.id, division_id=junior.id)
    volleyball_assignment = SeasonSportDivision(season_sport_id=volleyball_association.id, division_id=junior.id)
    other_assignment = SeasonSportDivision(season_sport_id=other_association.id, division_id=junior.id)
    db.session.add_all([junior_assignment, volleyball_assignment, other_assignment])
    db.session.flush()
    teams = [
        SeasonTeam(name="Other basketball", barangay="Demo", season_sport_division_id=junior_assignment.id),
        SeasonTeam(name="Archived basketball", barangay="Demo", season_sport_division_id=assignment_id, is_archived=True),
        SeasonTeam(name="Volleyball", barangay="Demo", season_sport_division_id=volleyball_assignment.id),
        SeasonTeam(name="Previous season", barangay="Demo", season_sport_division_id=other_assignment.id),
    ]
    db.session.add_all(teams)
    players = [
        Player(first_name=name, middle_name="", last_name="Demo", birthdate=date(date.today().year - 10, 1, 1),
               gender="MALE", address="Demo", is_archived=name == "Archived profile")
        for name in ("Current team", "Other division", "Archived team", "Other sport", "Other season", "Free", "Archived profile")
    ]
    db.session.add_all(players)
    db.session.flush()
    for player, assigned_team_id in zip(players[:5], [team_id, *[team.id for team in teams]]):
        db.session.add(Roster(season_team_id=assigned_team_id, player_id=player.id, jersey_number="1"))
    db.session.commit()

    url = f"/api/v1/season-teams/{team_id}/available-players"
    response = client.get(url)
    assert response.status_code == 200
    assert {player["id"] for player in response.get_json()["data"]} == {player.id for player in players[2:6]}
    rejected = client.post(
        f"/api/v1/season-teams/{team_id}/roster",
        json={"player_id": players[1].id, "jersey_number": "2"},
    )
    assert rejected.status_code == 409
    added = client.post(
        f"/api/v1/season-teams/{team_id}/roster",
        json={"player_id": players[5].id, "jersey_number": "2"},
    )
    assert added.status_code == 201
    assert players[5].id not in {player["id"] for player in client.get(url).get_json()["data"]}
    roster_id = added.get_json()["data"]["id"]
    assert client.delete(f"/api/v1/season-teams/{team_id}/roster/{roster_id}").status_code == 200
    assert players[5].id in {player["id"] for player in client.get(url).get_json()["data"]}

    assert client.get(f"/api/v1/season-teams/{teams[1].id}/available-players").status_code == 400
    assert client.get("/api/v1/season-teams/99999/available-players").status_code == 404
    client.post("/api/v1/auth/logout")
    assert client.get(url).status_code == 401
