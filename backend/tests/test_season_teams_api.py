from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Event

import pytest

from app import create_app
from app.application.rosters.services import RosterConflictError, RosterService
from app.application.teams.services import SeasonTeamConflictError, SeasonTeamService
from app.config.testing import TestingConfig
from app.domain.models.players import Player
from app.domain.models.roles import Role
from app.domain.models.rosters import Roster
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.users import User
from app.extensions import db
from app.infrastructure.database.roster_repository import RosterRepository
from app.infrastructure.database.season_team_repository import SeasonTeamRepository


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
    season_sport = SeasonSport(season_id=season_id, name=f"Sport {season_id}")
    db.session.add(season_sport)
    db.session.flush()
    division_assignment = SeasonSportDivision(
        season_sport_id=season_sport.id,
        name=f"Division {season_id}",
        gender_policy="ANY",
        minimum_roster_size=5,
        maximum_roster_size=15,
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


@pytest.mark.parametrize("status", ["PLANNING", "ONGOING", "COMPLETED", "ARCHIVED"])
def test_archive_and_restore_require_registration_status(client, status):
    login(client)
    season_id, assignment_id = create_division_assignment(client)
    team = SeasonTeam(name="Warriors", barangay="Demo", season_sport_division_id=assignment_id)
    db.session.add(team)
    db.session.commit()
    season = db.session.get(Season, season_id)
    season.season_status = status
    db.session.commit()
    url = f"/api/v1/season-teams/{team.id}"

    assert client.delete(url).status_code == 400
    assert client.patch(f"{url}/archive", json={"is_archived": True}).status_code == 400
    assert db.session.get(SeasonTeam, team.id).is_archived is False
    team.is_archived = True
    db.session.commit()
    assert client.patch(f"{url}/archive", json={"is_archived": False}).status_code == 400
    assert db.session.get(SeasonTeam, team.id).is_archived is True


def test_archive_allowed_outside_window_but_restore_requires_open_window(client):
    login(client)
    today = date.today()
    _, assignment_id = create_division_assignment(
        client, window_start=today - timedelta(days=4), window_end=today - timedelta(days=1),
    )
    team = SeasonTeam(name="Warriors", barangay="Demo", season_sport_division_id=assignment_id)
    db.session.add(team)
    db.session.commit()
    url = f"/api/v1/season-teams/{team.id}"

    assert client.delete(url).status_code == 200
    archived_at, archived_by = team.archived_at, team.archived_by
    assert archived_at is not None and archived_by is not None
    response = client.patch(f"{url}/archive", json={"is_archived": False})
    assert response.status_code == 400
    assert "registration window" in response.get_json()["message"]
    assert team.is_archived is True
    assert (team.archived_at, team.archived_by) == (archived_at, archived_by)


def test_restore_rejects_players_on_active_team_in_same_sport_and_season(client):
    login(client)
    _, assignment_id = create_division_assignment(client)
    assignment = db.session.get(SeasonSportDivision, assignment_id)
    other_assignment = SeasonSportDivision(
        season_sport_id=assignment.season_sport_id, name="Junior", gender_policy="ANY",
        minimum_roster_size=5, maximum_roster_size=15,
    )
    db.session.add(other_assignment)
    db.session.flush()
    teams = [
        SeasonTeam(name="Original", barangay="Demo", season_sport_division_id=assignment_id),
        SeasonTeam(name="New Team", barangay="Demo", season_sport_division_id=other_assignment.id),
    ]
    player = Player(
        first_name="Alex", middle_name="", last_name="Rivera",
        birthdate=date(2010, 1, 1), gender="MALE", address="Demo",
    )
    db.session.add_all([*teams, player])
    db.session.flush()
    db.session.add(Roster(season_team_id=teams[0].id, player_id=player.id, jersey_number="7"))
    db.session.commit()
    archive_url = f"/api/v1/season-teams/{teams[0].id}/archive"
    assert client.patch(archive_url, json={"is_archived": True}).status_code == 200
    old_metadata = (teams[0].archived_at, teams[0].archived_by)
    added = client.post(
        f"/api/v1/season-teams/{teams[1].id}/roster",
        json={"player_id": player.id, "jersey_number": "9"},
    )
    assert added.status_code == 201

    response = client.patch(archive_url, json={"is_archived": False})
    assert response.status_code == 409
    assert "Alex Rivera" in response.get_json()["message"]
    assert "New Team" in response.get_json()["message"]
    assert teams[0].is_archived is True
    assert (teams[0].archived_at, teams[0].archived_by) == old_metadata
    assert Roster.query.count() == 2

    assert client.delete(
        f"/api/v1/season-teams/{teams[1].id}/roster/{added.get_json()['data']['id']}"
    ).status_code == 200
    restored = client.patch(archive_url, json={"is_archived": False})
    assert restored.status_code == 200
    assert teams[0].is_archived is False
    assert teams[0].archived_at is None and teams[0].archived_by is None
    assert Roster.query.count() == 1


def test_restore_ignores_archived_teams_and_other_sports_or_seasons(client):
    login(client)
    season_id, assignment_id = create_division_assignment(client)
    assignment = db.session.get(SeasonSportDivision, assignment_id)
    other_season = Season(name="Other season", year=date.today().year, season_status="PLANNING")
    db.session.add(other_season)
    db.session.flush()
    associations = [
        SeasonSport(season_id=season_id, name="Other sport"),
        SeasonSport(season_id=other_season.id, name="Other season sport"),
    ]
    db.session.add_all(associations)
    db.session.flush()
    others = [SeasonSportDivision(season_sport_id=a.id, name="Senior", gender_policy="ANY",
                                  minimum_roster_size=5, maximum_roster_size=15) for a in associations]
    db.session.add_all(others)
    db.session.flush()
    teams = [
        SeasonTeam(name="Original", barangay="Demo", season_sport_division_id=assignment_id, is_archived=True),
        SeasonTeam(name="Archived", barangay="Demo", season_sport_division_id=assignment_id, is_archived=True),
        SeasonTeam(name="Other sport", barangay="Demo", season_sport_division_id=others[0].id),
        SeasonTeam(name="Other season", barangay="Demo", season_sport_division_id=others[1].id),
    ]
    player = Player(first_name="Alex", middle_name="", last_name="Rivera", birthdate=date(2010, 1, 1),
                    gender="MALE", address="Demo")
    db.session.add_all([*teams, player])
    db.session.flush()
    db.session.add_all([Roster(season_team_id=t.id, player_id=player.id, jersey_number="7") for t in teams])
    db.session.commit()

    response = client.patch(f"/api/v1/season-teams/{teams[0].id}/archive", json={"is_archived": False})
    assert response.status_code == 200
    assert teams[0].is_archived is False


def test_team_archive_endpoints_require_administrator(client):
    login(client)
    _, assignment_id = create_division_assignment(client)
    team = SeasonTeam(name="Warriors", barangay="Demo", season_sport_division_id=assignment_id)
    db.session.add(team)
    db.session.commit()
    url = f"/api/v1/season-teams/{team.id}"
    client.post("/api/v1/auth/logout")
    assert client.delete(url).status_code == 401
    login(client, "encoder", "encoder-pass-123")
    assert client.patch(f"{url}/archive", json={"is_archived": True}).status_code == 403
    assert client.delete(url).status_code == 403
    assert team.is_archived is False


@pytest.mark.parametrize("first_action", ["restore", "add"])
def test_concurrent_restore_and_roster_add_cannot_create_conflict(tmp_path, monkeypatch, first_action):
    database = (tmp_path / "restore-race.sqlite").as_posix()
    monkeypatch.setattr(TestingConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{database}")
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path / "sessions"), raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        role = Role(name="Administrator")
        db.session.add(role)
        db.session.flush()
        actor = User(username="admin", role_id=role.id, is_active=True)
        actor.set_password("password-123")
        season = Season(name="League", year=date.today().year, season_status="REGISTRATION")
        player = Player(first_name="Alex", middle_name="", last_name="Rivera",
                        birthdate=date(date.today().year - 10, 1, 1), gender="MALE", address="Demo")
        db.session.add_all([actor, season, player])
        db.session.flush()
        association = SeasonSport(season_id=season.id, name="Basketball")
        db.session.add(association)
        db.session.flush()
        assignment = SeasonSportDivision(season_sport_id=association.id, name="Senior", gender_policy="ANY",
                                         minimum_roster_size=1, maximum_roster_size=15)
        db.session.add(assignment)
        db.session.flush()
        original = SeasonTeam(name="Original", barangay="Demo", season_sport_division_id=assignment.id, is_archived=True)
        other = SeasonTeam(name="Other", barangay="Demo", season_sport_division_id=assignment.id)
        db.session.add_all([original, other])
        db.session.flush()
        db.session.add(Roster(season_team_id=original.id, player_id=player.id, jersey_number="7"))
        db.session.commit()
        original_id, other_id, player_id, actor_id = original.id, other.id, player.id, actor.id
        association_updated_at = association.updated_at

    first_locked = Event()
    second_started = Event()
    team_lock = SeasonTeamRepository.lock_team_roster
    roster_lock = RosterRepository.lock_team_roster

    def lock_for_restore(repository, team_id):
        team_lock(repository, team_id)
        if first_action == "restore":
            first_locked.set()
            assert second_started.wait(timeout=10)

    def lock_for_add(repository, team_id):
        roster_lock(repository, team_id)
        if first_action == "add":
            first_locked.set()
            assert second_started.wait(timeout=10)

    monkeypatch.setattr(SeasonTeamRepository, "lock_team_roster", lock_for_restore)
    monkeypatch.setattr(RosterRepository, "lock_team_roster", lock_for_add)

    def perform(action):
        with app.app_context():
            if action != first_action:
                assert first_locked.wait(timeout=10)
                second_started.set()
            try:
                if action == "restore":
                    SeasonTeamService().set_archived(original_id, False, actor_id)
                else:
                    RosterService().add_player(other_id, player_id=player_id, jersey_number="9", actor_id=actor_id)
                return "success"
            except (SeasonTeamConflictError, RosterConflictError):
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(perform, ["restore", "add"]))
    assert results == (["success", "conflict"] if first_action == "restore" else ["conflict", "success"])
    with app.app_context():
        active_entries = (
            db.session.query(Roster)
            .join(SeasonTeam, SeasonTeam.id == Roster.season_team_id)
            .filter(Roster.player_id == player_id, SeasonTeam.is_archived.is_(False))
            .count()
        )
        assert active_entries == 1
        assert SeasonSport.query.one().updated_at == association_updated_at
        db.session.remove()
        db.drop_all()
