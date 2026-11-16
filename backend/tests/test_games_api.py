import importlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Barrier

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from app import create_app
from app.application.games.services import GameService, ScheduleConflictError
from app.config.testing import TestingConfig
from app.domain.models.divisions import Division
from app.domain.models.games import Game, ScheduleLock
from app.domain.models.roles import Role
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.sports import Sport
from app.domain.models.users import User
from app.extensions import db


@pytest.fixture()
def context(tmp_path, monkeypatch):
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path), raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        admin_role = Role(name="Administrator")
        encoder_role = Role(name="Encoder")
        db.session.add_all([ScheduleLock(id=1), admin_role, encoder_role])
        db.session.flush()
        for username, role in (("admin", admin_role), ("encoder", encoder_role)):
            user = User(username=username, role_id=role.id, is_active=True)
            user.set_password("password-123")
            db.session.add(user)
        season = Season(name="League", year=2026, season_status="ONGOING")
        sport = Sport(name="Basketball")
        divisions = [
            Division(name=name, gender_policy="ANY", minimum_roster_size=5, maximum_roster_size=15)
            for name in ("Senior", "Junior")
        ]
        db.session.add_all([season, sport, *divisions])
        db.session.flush()
        association = SeasonSport(season_id=season.id, sport_id=sport.id)
        db.session.add(association)
        db.session.flush()
        assignments = [
            SeasonSportDivision(season_sport_id=association.id, division_id=division.id)
            for division in divisions
        ]
        db.session.add_all(assignments)
        db.session.flush()
        teams = [
            SeasonTeam(name=name, barangay="Demo", season_sport_division_id=assignment.id)
            for name, assignment in (("A", assignments[0]), ("B", assignments[0]),
                                     ("C", assignments[0]), ("D", assignments[0]),
                                     ("Junior A", assignments[1]), ("Junior B", assignments[1]))
        ]
        db.session.add_all(teams)
        db.session.commit()
        yield app.test_client(), season, assignments, teams
        db.session.remove()
        db.drop_all()


def login(client, username="admin"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": "password-123"})


def payload(teams, **overrides):
    data = {
        "home_team_id": teams[0].id,
        "away_team_id": teams[1].id,
        "venue": "Barangay Court",
        "starts_at": "2027-01-03T10:00",
        "ends_at": "2027-01-03T11:00",
    }
    data.update(overrides)
    return data


@pytest.fixture()
def reschedule_clock(monkeypatch):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2027, 1, 1, 9, 0, tzinfo=tz)

    monkeypatch.setattr("app.application.games.services.datetime", FrozenDatetime)


def reschedule_payload(**overrides):
    data = {
        "venue": "Barangay Court",
        "starts_at": "2027-01-03T10:00",
        "ends_at": "2027-01-03T11:00",
    }
    data.update(overrides)
    return data


def test_reschedule_preserves_teams_and_excludes_the_current_game(context, reschedule_clock):
    client, _, assignments, teams = context
    login(client)
    games_url = f"/api/v1/season-sport-divisions/{assignments[0].id}/games"
    original = client.post(games_url, json=payload(teams)).get_json()["data"]
    url = f"/api/v1/games/{original['id']}/schedule"

    unchanged = client.put(url, json=reschedule_payload())
    assert unchanged.status_code == 200
    changed = client.put(url, json=reschedule_payload(
        venue="  New   Court ", starts_at="2027-01-03T10:30", ends_at="2027-01-03T11:30"
    ))
    assert changed.status_code == 200
    result = changed.get_json()["data"]
    assert result["id"] == original["id"]
    assert (result["home_team_id"], result["away_team_id"]) == (teams[0].id, teams[1].id)
    assert (result["venue"], result["starts_at"], result["ends_at"]) == (
        "New Court", "2027-01-03T10:30:00", "2027-01-03T11:30:00"
    )
    assert client.get(games_url).get_json()["data"] == [result]
    assert Game.query.count() == 1


def test_reschedule_requires_admin_ongoing_and_unstarted_game(context, reschedule_clock):
    client, season, assignments, teams = context
    login(client)
    created = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)
    ).get_json()["data"]
    url = f"/api/v1/games/{created['id']}/schedule"
    client.post("/api/v1/auth/logout")
    assert client.put(url, json=reschedule_payload()).status_code == 401
    login(client, "encoder")
    assert client.put(url, json=reschedule_payload()).status_code == 403
    login(client)
    assert client.put("/api/v1/games/99999/schedule", json=reschedule_payload()).status_code == 404

    season.season_status = "REGISTRATION"
    db.session.commit()
    assert client.put(url, json=reschedule_payload()).status_code == 400
    season.season_status = "ONGOING"
    game = db.session.get(Game, created["id"])
    game.starts_at = datetime(2027, 1, 1, 9)
    game.ends_at = datetime(2027, 1, 1, 10)
    db.session.commit()
    assert client.put(url, json=reschedule_payload()).status_code == 400
    assert game.starts_at == datetime(2027, 1, 1, 9)


def test_reschedule_rejects_team_and_venue_conflicts_but_allows_adjacent_times(context, reschedule_clock):
    client, _, assignments, teams = context
    login(client)
    senior = f"/api/v1/season-sport-divisions/{assignments[0].id}/games"
    junior = f"/api/v1/season-sport-divisions/{assignments[1].id}/games"
    original = client.post(senior, json=payload(teams)).get_json()["data"]
    assert client.post(senior, json=payload(
        teams, away_team_id=teams[2].id, venue="Other Court",
        starts_at="2027-01-03T12:00", ends_at="2027-01-03T13:00",
    )).status_code == 201
    assert client.post(junior, json=payload(
        teams, home_team_id=teams[4].id, away_team_id=teams[5].id,
        venue="Shared Court", starts_at="2027-01-03T14:00", ends_at="2027-01-03T15:00",
    )).status_code == 201
    url = f"/api/v1/games/{original['id']}/schedule"
    assert client.put(url, json=reschedule_payload(
        venue="Different Court", starts_at="2027-01-03T12:30", ends_at="2027-01-03T13:30",
    )).status_code == 409
    assert client.put(url, json=reschedule_payload(
        venue=" shared   COURT ", starts_at="2027-01-03T14:30", ends_at="2027-01-03T15:30",
    )).status_code == 409
    assert db.session.get(Game, original["id"]).starts_at == datetime(2027, 1, 3, 10)
    assert client.put(url, json=reschedule_payload(
        venue="Shared Court", starts_at="2027-01-03T15:00", ends_at="2027-01-03T16:00",
    )).status_code == 200


@pytest.mark.parametrize("changes", [
    {"venue": " "},
    {"starts_at": "2027-01-03T11:00", "ends_at": "2027-01-03T11:00"},
    {"starts_at": "2027-01-01T09:00", "ends_at": "2027-01-01T10:00"},
    {"starts_at": "2027-01-03T10:00:00+08:00"},
    {"starts_at": "2027-01-03T10:00:00.500"},
    {"home_team_id": 999},
])
def test_reschedule_rejects_invalid_input_without_changing_game(context, reschedule_clock, changes):
    client, _, assignments, teams = context
    login(client)
    original = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)
    ).get_json()["data"]
    response = client.put(
        f"/api/v1/games/{original['id']}/schedule", json=reschedule_payload(**changes)
    )
    assert response.status_code == 400
    assert db.session.get(Game, original["id"]).to_dict() == original


def test_reschedule_requires_complete_json_and_schedule_lock(context, reschedule_clock):
    client, _, assignments, teams = context
    login(client)
    original = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)
    ).get_json()["data"]
    url = f"/api/v1/games/{original['id']}/schedule"
    assert client.put(url, json=[]).status_code == 400
    assert client.put(url, json={"venue": "Court"}).status_code == 400
    db.session.delete(db.session.get(ScheduleLock, 1))
    db.session.commit()
    with pytest.raises(RuntimeError, match="Schedule lock is missing"):
        client.put(url, json=reschedule_payload())
    assert db.session.get(Game, original["id"]).to_dict() == original


def test_schedule_and_public_list_are_division_specific_and_ordered(context):
    client, _, assignments, teams = context
    login(client)
    endpoint = f"/api/v1/season-sport-divisions/{assignments[0].id}/games"
    first = client.post(endpoint, json=payload(teams))
    second = client.post(endpoint, json=payload(
        teams, venue="Other Court", starts_at="2027-01-03T09:00", ends_at="2027-01-03T10:00"
    ))
    assert first.status_code == second.status_code == 201
    client.post("/api/v1/auth/logout")
    response = client.get(endpoint)
    assert response.status_code == 200
    assert [game["id"] for game in response.get_json()["data"]] == [
        second.get_json()["data"]["id"], first.get_json()["data"]["id"]
    ]
    assert client.get(f"/api/v1/season-sport-divisions/{assignments[1].id}/games").get_json()["data"] == []
    assert client.get("/api/v1/season-sport-divisions/99999/games").status_code == 404


def test_requires_admin_ongoing_season_and_active_distinct_division_teams(context):
    client, season, assignments, teams = context
    endpoint = f"/api/v1/season-sport-divisions/{assignments[0].id}/games"
    assert client.post(endpoint, json=payload(teams)).status_code == 401
    login(client, "encoder")
    assert client.post(endpoint, json=payload(teams)).status_code == 403
    login(client)
    season.season_status = "REGISTRATION"
    db.session.commit()
    assert client.post(endpoint, json=payload(teams)).status_code == 400
    season.season_status = "ONGOING"
    teams[1].is_archived = True
    db.session.commit()
    assert client.post(endpoint, json=payload(teams)).status_code == 400
    assert client.post(endpoint, json=payload(teams, away_team_id=teams[4].id)).status_code == 400
    assert client.post(endpoint, json=payload(teams, away_team_id=teams[0].id)).status_code == 400
    assert client.post(endpoint, json=payload(teams, away_team_id=99999)).status_code == 404
    assert Game.query.count() == 0


def test_blocks_team_and_normalized_venue_overlaps_across_divisions(context):
    client, _, assignments, teams = context
    login(client)
    senior = f"/api/v1/season-sport-divisions/{assignments[0].id}/games"
    junior = f"/api/v1/season-sport-divisions/{assignments[1].id}/games"
    assert client.post(senior, json=payload(teams)).status_code == 201
    assert client.post(senior, json=payload(
        teams, away_team_id=teams[2].id, venue="Other", starts_at="2027-01-03T10:30", ends_at="2027-01-03T11:30"
    )).status_code == 409
    assert client.post(junior, json=payload(
        teams, home_team_id=teams[4].id, away_team_id=teams[5].id,
        venue="  BARANGAY   court ", starts_at="2027-01-03T09:30", ends_at="2027-01-03T10:30"
    )).status_code == 409
    assert client.post(junior, json=payload(
        teams, home_team_id=teams[4].id, away_team_id=teams[5].id,
        venue="barangay court", starts_at="2027-01-03T11:00", ends_at="2027-01-03T12:00"
    )).status_code == 201


@pytest.mark.parametrize("changes", [
    {"venue": "   "},
    {"starts_at": "2027-01-03T11:00", "ends_at": "2027-01-03T11:00"},
    {"starts_at": "2027-01-03T10:00:00+08:00"},
    {"starts_at": "2027-01-03T10:00:00.500"},
    {"starts_at": "not-a-date"},
])
def test_rejects_invalid_input(context, changes):
    client, _, assignments, teams = context
    login(client)
    response = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams, **changes)
    )
    assert response.status_code == 400
    assert Game.query.count() == 0


def test_missing_schedule_lock_fails_without_inserting(context):
    client, _, assignments, teams = context
    login(client)
    db.session.delete(db.session.get(ScheduleLock, 1))
    db.session.commit()
    with pytest.raises(RuntimeError, match="Schedule lock is missing"):
        client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams))
    assert Game.query.count() == 0


def test_game_migration_adds_and_removes_tables():
    migration = importlib.import_module("migrations.versions.b73e19f26d42_add_game_scheduling")
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE season_sport_divisions (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE season_teams (id INTEGER PRIMARY KEY)"))
        operations = Operations(MigrationContext.configure(connection))
        with Operations.context(operations.migration_context):
            migration.upgrade()
            assert connection.execute(text("SELECT id FROM schedule_lock")).scalar_one() == 1
            assert "games" in inspect(connection).get_table_names()
            migration.downgrade()
            assert "games" not in inspect(connection).get_table_names()
            assert "schedule_lock" not in inspect(connection).get_table_names()
    engine.dispose()


def test_concurrent_schedule_requests_cannot_book_same_team(tmp_path, monkeypatch):
    database = (tmp_path / "concurrent.sqlite").as_posix()
    monkeypatch.setattr(TestingConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{database}")
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path / "sessions"), raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        season = Season(name="Concurrent", year=2026, season_status="ONGOING")
        sport = Sport(name="Basketball")
        division = Division(name="Senior", gender_policy="ANY", minimum_roster_size=5, maximum_roster_size=15)
        db.session.add_all([ScheduleLock(id=1), season, sport, division])
        db.session.flush()
        association = SeasonSport(season_id=season.id, sport_id=sport.id)
        db.session.add(association)
        db.session.flush()
        assignment = SeasonSportDivision(season_sport_id=association.id, division_id=division.id)
        db.session.add(assignment)
        db.session.flush()
        teams = [
            SeasonTeam(name=name, barangay="Demo", season_sport_division_id=assignment.id)
            for name in ("A", "B", "C")
        ]
        db.session.add_all(teams)
        db.session.commit()
        assignment_id, team_ids = assignment.id, [team.id for team in teams]

    start = Barrier(2)

    def book(index):
        with app.app_context():
            start.wait(timeout=10)
            try:
                GameService().schedule_game(
                    assignment_id,
                    home_team_id=team_ids[0],
                    away_team_id=team_ids[index + 1],
                    venue=f"Court {index}",
                    starts_at=datetime(2027, 1, 3, 10),
                    ends_at=datetime(2027, 1, 3, 11),
                )
                return "created"
            except ScheduleConflictError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(book, range(2)))
    assert sorted(results) == ["conflict", "created"]
    with app.app_context():
        assert Game.query.count() == 1
        db.session.remove()
        db.drop_all()


def test_concurrent_reschedule_and_creation_cannot_book_same_team(tmp_path, monkeypatch, reschedule_clock):
    database = (tmp_path / "concurrent-reschedule.sqlite").as_posix()
    monkeypatch.setattr(TestingConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{database}")
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path / "sessions"), raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        season = Season(name="Concurrent", year=2026, season_status="ONGOING")
        sport = Sport(name="Basketball")
        division = Division(name="Senior", gender_policy="ANY", minimum_roster_size=5, maximum_roster_size=15)
        db.session.add_all([ScheduleLock(id=1), season, sport, division])
        db.session.flush()
        association = SeasonSport(season_id=season.id, sport_id=sport.id)
        db.session.add(association)
        db.session.flush()
        assignment = SeasonSportDivision(season_sport_id=association.id, division_id=division.id)
        db.session.add(assignment)
        db.session.flush()
        teams = [
            SeasonTeam(name=name, barangay="Demo", season_sport_division_id=assignment.id)
            for name in ("A", "B", "C")
        ]
        db.session.add_all(teams)
        db.session.flush()
        assignment_id, team_ids = assignment.id, [team.id for team in teams]
        game = GameService().schedule_game(
            assignment_id, home_team_id=team_ids[0], away_team_id=team_ids[1],
            venue="Original Court", starts_at=datetime(2027, 1, 3, 10), ends_at=datetime(2027, 1, 3, 11),
        )
        game_id = game.id

    start = Barrier(2)

    def book(index):
        with app.app_context():
            start.wait(timeout=10)
            try:
                service = GameService()
                if index == 0:
                    service.reschedule_game(
                        game_id, venue="New Court",
                        starts_at=datetime(2027, 1, 4, 10), ends_at=datetime(2027, 1, 4, 11),
                    )
                else:
                    service.schedule_game(
                        assignment_id, home_team_id=team_ids[0], away_team_id=team_ids[2],
                        venue="Another Court",
                        starts_at=datetime(2027, 1, 4, 10), ends_at=datetime(2027, 1, 4, 11),
                    )
                return "saved"
            except ScheduleConflictError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(book, range(2)))
    assert sorted(results) == ["conflict", "saved"]
    with app.app_context():
        assert Game.query.filter_by(starts_at=datetime(2027, 1, 4, 10)).count() == 1
        db.session.remove()
        db.drop_all()
