import importlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from threading import Barrier

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from app import create_app
from app.application.games.services import GameService, ScheduleConflictError
from app.application.games.policies import GamePolicy
from app.application.games.types import DivisionSnapshot, GameData, SeasonSnapshot, StandingTeam, TeamSnapshot
from app.config.testing import TestingConfig
from app.domain.models.games import Game, GameResultReopening, ScheduleLock
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.roles import Role
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_sports import SeasonSport
from app.domain.models.seasons import Season
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.users import User
from app.extensions import db
from app.infrastructure.database.game_repository import GameRepository


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
        db.session.add(season)
        db.session.flush()
        association = SeasonSport(season_id=season.id, name="Basketball")
        db.session.add(association)
        db.session.flush()
        assignments = [
            SeasonSportDivision(season_sport_id=association.id, name=name, gender_policy="ANY",
                                minimum_roster_size=5, maximum_roster_size=15)
            for name in ("Senior", "Junior")
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


def test_repository_returns_game_validation_snapshots(context):
    _, season, assignments, teams = context
    repository = GameRepository()

    division = repository.get_division_assignment(assignments[0].id)
    assert division == DivisionSnapshot(season_sport_id=assignments[0].season_sport_id)
    assert division is not None
    assert repository.get_season_for_update(division) == SeasonSnapshot(season_status=season.season_status)
    assert repository.get_team_for_update(teams[0].id) == TeamSnapshot(
        season_sport_division_id=assignments[0].id, is_archived=False,
    )
    assert repository.get_division_assignment(99999) is None
    assert repository.get_team_for_update(99999) is None
    assert repository.get_season_for_update(DivisionSnapshot(season_sport_id=99999)) is None


@pytest.fixture()
def result_clock(monkeypatch):
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2027, 1, 4, tzinfo=tz)

        @classmethod
        def utcnow(cls):
            return cls(2027, 1, 4)

    monkeypatch.setattr("app.application.games.services.datetime", FrozenDatetime)


def configure_statistics(client, sport_id, *, scoring=True, team_points=False):
    response = client.put(f"/api/v1/season-sports/{sport_id}/statistics-configuration", json={
        "allow_team_points": team_points,
        "types": [{"name": "Points" if scoring else "Kills", "abbreviation": "PTS" if scoring else "K",
                   "required": True, "is_scoring": scoring}],
    })
    assert response.status_code == 200
    return response.get_json()["data"]["types"][0]["id"]


def add_stat_rosters(teams):
    for index, team in enumerate(teams):
        player = Player(first_name=f"Player{index}", last_name="Example", middle_name="",
                        birthdate=date(2000, 1, 1), gender="MALE", address="Demo")
        db.session.add(player)
        db.session.flush()
        db.session.add(Roster(season_team_id=team.id, player_id=player.id, jersey_number=str(index + 1)))
    db.session.commit()


def write_stats(client, game_id, stat_id, scores):
    data = client.get(f"/api/v1/games/{game_id}/statistics").get_json()["data"]
    teams = []
    for team, score in zip(data["teams"], scores):
        teams.append({"team_id": team["team_id"], "team_points": None, "players": [
            {"player_id": player["player_id"], "status": "PLAYED", "values": {str(stat_id): str(score)}}
            for player in team["players"]
        ]})
    return client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": teams})


def test_result_lifecycle_standings_and_reopening_history(context, result_clock):
    client, season, assignments, teams = context
    login(client)
    division = assignments[0].id
    game = client.post(f"/api/v1/season-sport-divisions/{division}/games", json=payload(teams)).get_json()["data"]
    game_id = game["id"]
    standings_url = f"/api/v1/season-sport-divisions/{division}/standings"
    initial = client.get(standings_url).get_json()["data"]
    assert len(initial) == 4 and all(row["wins"] == row["losses"] == 0 for row in initial)
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    client.post("/api/v1/auth/logout")
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 85, "away_score": 80}).status_code == 401
    login(client, "encoder")
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 80, "away_score": 80}).status_code == 400
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 85, "away_score": 80}).status_code == 200
    assert client.get(standings_url).get_json()["data"] == initial
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 403
    login(client)
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    stat_id = configure_statistics(client, assignments[0].season_sport_id)
    add_stat_rosters(teams[:2])
    assert write_stats(client, game_id, stat_id, (85, 80)).status_code == 200
    result = client.post(f"/api/v1/games/{game_id}/finalize")
    assert result.status_code == 200
    assert result.get_json()["data"]["result_status"] == "FINALIZED"
    standings = {row["team_id"]: row for row in client.get(standings_url).get_json()["data"]}
    assert (standings[teams[0].id]["wins"], standings[teams[1].id]["losses"]) == (1, 1)
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 70, "away_score": 90}).status_code == 400
    assert client.post(f"/api/v1/games/{game_id}/reopen", json={"reason": "  "}).status_code == 400
    assert client.post(f"/api/v1/games/{game_id}/reopen", json={"reason": "Score sheet correction"}).status_code == 200
    history = GameResultReopening.query.one()
    assert (history.reason, history.home_score, history.away_score) == ("Score sheet correction", 85, 80)
    assert history.reopened_by == history.finalized_by and history.finalized_at is not None
    assert client.get(standings_url).get_json()["data"] == initial
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 70, "away_score": 90}).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    assert write_stats(client, game_id, stat_id, (70, 90)).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 200
    standings = {row["team_id"]: row for row in client.get(standings_url).get_json()["data"]}
    assert (standings[teams[0].id]["losses"], standings[teams[1].id]["wins"]) == (1, 1)
    season.season_status = "COMPLETED"
    db.session.commit()
    assert client.post(f"/api/v1/games/{game_id}/reopen", json={"reason": "Correction"}).status_code == 400


def test_statistics_dnp_matching_and_locked_configuration(context, result_clock):
    client, _, assignments, teams = context
    login(client)
    game = client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)).get_json()["data"]
    game_id = game["id"]
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 7, "away_score": 4}).status_code == 200
    stat_id = configure_statistics(client, assignments[0].season_sport_id, team_points=True)
    add_stat_rosters([teams[0], teams[1], teams[0]])
    data = client.get(f"/api/v1/games/{game_id}/statistics").get_json()["data"]
    payload_teams = []
    for team, points in zip(data["teams"], (6, 4)):
        players = [{"player_id": p["player_id"], "status": "PLAYED", "values": {str(stat_id): str(points)}}
                   for p in team["players"]]
        if len(players) > 1:
            players[1] = {"player_id": players[1]["player_id"], "status": "DNP", "values": {}}
        payload_teams.append({"team_id": team["team_id"], "team_points": 0, "players": players})
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": payload_teams}).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    payload_teams[0]["team_points"] = 1
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": payload_teams}).status_code == 200
    config_url = f"/api/v1/season-sports/{assignments[0].season_sport_id}/statistics-configuration"
    assert client.get(config_url).get_json()["data"]["locked"] is True
    assert client.put(config_url, json={"allow_team_points": False, "types": [
        {"name": "Other", "abbreviation": "O", "required": True, "is_scoring": False},
    ]}).status_code == 400
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 200
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": payload_teams}).status_code == 400


def test_statistics_optional_score_matching_supports_objective_games(context, result_clock):
    client, _, assignments, teams = context
    login(client)
    game = client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)).get_json()["data"]
    game_id = game["id"]
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 1, "away_score": 2}).status_code == 200
    stat_id = configure_statistics(client, assignments[0].season_sport_id, scoring=False)
    add_stat_rosters(teams[:2])
    assert write_stats(client, game_id, stat_id, (45, 30)).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 200
    rows = {r["team_id"]: r for r in client.get(f"/api/v1/season-sport-divisions/{assignments[0].id}/standings").get_json()["data"]}
    assert rows[teams[1].id]["wins"] == 1


def test_existing_finalized_result_counts_until_reopened(context, result_clock):
    client, _, assignments, teams = context
    login(client)
    game_id = client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)).get_json()["data"]["id"]
    game = db.session.get(Game, game_id)
    game.result_status = "FINALIZED"
    game.home_score, game.away_score = 10, 8
    game.finalized_by = User.query.filter_by(username="admin").one().id
    game.finalized_at = datetime(2027, 1, 4)
    db.session.commit()
    standings_url = f"/api/v1/season-sport-divisions/{assignments[0].id}/standings"
    assert next(row for row in client.get(standings_url).get_json()["data"] if row["team_id"] == teams[0].id)["wins"] == 1
    assert client.post(f"/api/v1/games/{game_id}/reopen", json={"reason": "Correction"}).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    assert all(row["wins"] == 0 for row in client.get(standings_url).get_json()["data"])


def test_statistics_permissions_validation_and_partial_entries(context, result_clock):
    client, _, assignments, teams = context
    config_url = f"/api/v1/season-sports/{assignments[0].season_sport_id}/statistics-configuration"
    configuration = {"allow_team_points": False, "types": [
        {"name": "Points", "abbreviation": "PTS", "required": True, "is_scoring": True},
        {"name": "Assists", "abbreviation": "AST", "required": True, "is_scoring": False},
    ]}
    assert client.put(config_url, json=configuration).status_code == 401
    login(client, "encoder")
    assert client.put(config_url, json=configuration).status_code == 403
    login(client)
    bad = {**configuration, "allow_team_points": True, "types": [{**configuration["types"][0], "is_scoring": False}]}
    assert client.put(config_url, json=bad).status_code == 400
    result = client.put(config_url, json=configuration)
    assert result.status_code == 200
    points, assists = [str(item["id"]) for item in result.get_json()["data"]["types"]]
    add_stat_rosters(teams[:2])
    game_id = client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)).get_json()["data"]["id"]
    assert client.put(f"/api/v1/games/{game_id}/result", json={"home_score": 8, "away_score": 3}).status_code == 200
    data = client.get(f"/api/v1/games/{game_id}/statistics").get_json()["data"]
    entries = [{"team_id": t["team_id"], "team_points": None, "players": [
        {"player_id": p["player_id"], "status": "PLAYED", "values": {points: score}}
        for p in t["players"]]} for t, score in zip(data["teams"], ("8", "3"))]
    entries[0]["players"][0]["values"][points] = "1e999999999"
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": entries}).status_code == 400
    assert client.get(config_url).get_json()["data"]["locked"] is False
    entries[0]["players"][0]["values"][points] = "8"
    entries[0]["players"][0]["status"] = "DNP"
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": entries}).status_code == 400
    entries[0]["players"][0]["status"] = "PLAYED"
    entries[1]["players"][0]["player_id"] = entries[0]["players"][0]["player_id"]
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": entries}).status_code == 400
    entries[1]["players"][0]["player_id"] = data["teams"][1]["players"][0]["player_id"]
    login(client, "encoder")
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": entries}).status_code == 200
    login(client)
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 400
    for team in entries:
        team["players"][0]["values"][assists] = "0"
    assert client.put(f"/api/v1/games/{game_id}/statistics", json={"teams": entries}).status_code == 200
    assert client.post(f"/api/v1/games/{game_id}/finalize").status_code == 200


def test_statistics_migration_preserves_finalized_results():
    migration = importlib.import_module("migrations.versions.a6b7c8d9e012_player_game_statistics")
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        for table in ("season_sports", "season_teams", "players"):
            connection.execute(text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY)"))
            connection.execute(text(f"INSERT INTO {table} VALUES (1)"))
        connection.execute(text("CREATE TABLE games (id INTEGER PRIMARY KEY, result_status VARCHAR(20), home_score INTEGER, away_score INTEGER)"))
        connection.execute(text("INSERT INTO games VALUES (1, 'FINALIZED', 10, 8)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text("SELECT result_status,home_score,away_score FROM games")).one() == ("FINALIZED", 10, 8)
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert {"sport_statistic_configurations", "statistic_types", "game_participants",
                "player_game_statistics", "game_team_points"} <= set(inspect(connection).get_table_names())
        with pytest.raises(RuntimeError, match="restore"):
            migration.downgrade()
    engine.dispose()


def test_result_cannot_be_entered_before_game_end(context, reschedule_clock):
    client, _, assignments, teams = context
    login(client)
    game = client.post(f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams)).get_json()["data"]
    response = client.put(f"/api/v1/games/{game['id']}/result", json={"home_score": 5, "away_score": 4})
    assert response.status_code == 400
    assert response.get_json()["message"] == "Game results can only be entered after the scheduled end."


def test_standings_head_to_head_multiteam_and_unplayed():
    teams = [StandingTeam(i, str(i), False) for i in range(1, 8)]
    def game(home: int, away: int) -> GameData:
        return GameData(id=1, season_sport_division_id=1, home_team_id=home, away_team_id=away,
                        venue="Court", starts_at="", ends_at="", result_status="FINALIZED",
                        home_score=1, away_score=0, finalized_at=None, finalized_by=None)
    # 1, 2 and 3 each have two wins. Among them: 1 beats 2; 2 beats 3.
    # Team 4 also has two wins, but no games against the tied group.
    games = [game(1, 2), game(2, 3), game(1, 5), game(2, 5), game(3, 5),
             game(3, 6), game(4, 6), game(4, 7)]
    result = GamePolicy().calculate_standings(teams, games)
    assert [(r["team_id"], r["rank"]) for r in result[:4]] == [(1, 1), (2, 2), (3, 3), (4, 4)]
    assert result[-1]["wins"] == 0


def test_game_results_migration_preserves_existing_game_with_foreign_keys():
    migration = importlib.import_module("migrations.versions.f5a6b7c8d901_game_results")
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE games (id INTEGER PRIMARY KEY, venue VARCHAR(150) NOT NULL)"))
        connection.execute(text("INSERT INTO games VALUES (1, 'Court')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text("SELECT id, venue, result_status, home_score FROM games")).one() == (1, "Court", "SCHEDULED", None)
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert "game_result_reopenings" in inspect(connection).get_table_names()
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            migration.downgrade()
    engine.dispose()


def test_scheduling_reports_missing_division_and_season(context, monkeypatch):
    client, _, assignments, teams = context
    login(client)
    missing_division = client.post(
        "/api/v1/season-sport-divisions/99999/games", json=payload(teams),
    )
    assert missing_division.status_code == 404
    assert missing_division.get_json()["message"] == "Season division assignment not found."

    monkeypatch.setattr(GameRepository, "get_season_for_update", lambda self, assignment: None)
    missing_season = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams),
    )
    assert missing_season.status_code == 404
    assert missing_season.get_json()["message"] == "Season not found for division assignment."
    assert Game.query.count() == 0


def test_scheduling_uses_injected_repository_for_overlap_query(context):
    _, _, assignments, teams = context

    class ConflictingRepository(GameRepository):
        def has_overlap(self, *args, **kwargs):
            return True

    with pytest.raises(ScheduleConflictError):
        GameService(repository=ConflictingRepository()).schedule_game(
            assignments[0].id, home_team_id=teams[0].id, away_team_id=teams[1].id,
            venue="Court", starts_at=datetime(2027, 1, 3, 10), ends_at=datetime(2027, 1, 3, 11),
        )
    assert Game.query.count() == 0


def test_scheduling_rolls_back_unexpected_write_errors(context, monkeypatch):
    _, _, assignments, teams = context
    original_add = GameRepository.add_game

    def fail_after_add(repository, *args, **kwargs):
        original_add(repository, *args, **kwargs)
        raise RuntimeError("simulated schedule failure")

    monkeypatch.setattr(GameRepository, "add_game", fail_after_add)
    with pytest.raises(RuntimeError, match="simulated schedule failure"):
        GameService().schedule_game(
            assignments[0].id,
            home_team_id=teams[0].id,
            away_team_id=teams[1].id,
            venue="Court",
            starts_at=datetime(2027, 1, 3, 10),
            ends_at=datetime(2027, 1, 3, 11),
        )
    assert Game.query.count() == 0


def test_rescheduling_rolls_back_when_commit_fails(context, monkeypatch, reschedule_clock):
    _, _, assignments, teams = context
    original_game = GameService().schedule_game(
        assignments[0].id,
        home_team_id=teams[0].id,
        away_team_id=teams[1].id,
        venue="Court",
        starts_at=datetime(2027, 1, 3, 10),
        ends_at=datetime(2027, 1, 3, 11),
    )
    original_schedule = (
        original_game["venue"],
        original_game["starts_at"],
        original_game["ends_at"],
    )

    def fail_commit():
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db.session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated commit failure"):
        GameService().reschedule_game(
            original_game["id"],
            venue="New Court",
            starts_at=datetime(2027, 1, 3, 10, 30),
            ends_at=datetime(2027, 1, 3, 11, 30),
        )

    game = db.session.get(Game, original_game["id"])
    assert (
        game.venue,
        game.starts_at.isoformat(),
        game.ends_at.isoformat(),
    ) == original_schedule


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


def test_venue_conflicts_across_seasons(context):
    client, _, assignments, teams = context
    login(client)
    original = client.post(
        f"/api/v1/season-sport-divisions/{assignments[0].id}/games", json=payload(teams),
    )
    assert original.status_code == 201
    season = Season(name="Other season", year=2027, season_status="ONGOING")
    db.session.add(season)
    db.session.flush()
    sport = SeasonSport(season_id=season.id, name="Basketball")
    db.session.add(sport)
    db.session.flush()
    division = SeasonSportDivision(season_sport_id=sport.id, name="Senior", gender_policy="ANY",
                                   minimum_roster_size=5, maximum_roster_size=15)
    db.session.add(division)
    db.session.flush()
    other_teams = [SeasonTeam(name=name, barangay="Demo", season_sport_division_id=division.id)
                   for name in ("Other A", "Other B")]
    db.session.add_all(other_teams)
    db.session.commit()
    response = client.post(
        f"/api/v1/season-sport-divisions/{division.id}/games",
        json=payload(other_teams, venue="  barangay   court  "),
    )
    assert response.status_code == 409
    assert Game.query.count() == 1


def test_concurrent_schedule_requests_cannot_book_same_team(tmp_path, monkeypatch):
    database = (tmp_path / "concurrent.sqlite").as_posix()
    monkeypatch.setattr(TestingConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{database}")
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path / "sessions"), raising=False)
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        season = Season(name="Concurrent", year=2026, season_status="ONGOING")
        db.session.add_all([ScheduleLock(id=1), season])
        db.session.flush()
        association = SeasonSport(season_id=season.id, name="Basketball")
        db.session.add(association)
        db.session.flush()
        assignment = SeasonSportDivision(season_sport_id=association.id, name="Senior", gender_policy="ANY",
                                         minimum_roster_size=5, maximum_roster_size=15)
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
        db.session.add_all([ScheduleLock(id=1), season])
        db.session.flush()
        association = SeasonSport(season_id=season.id, name="Basketball")
        db.session.add(association)
        db.session.flush()
        assignment = SeasonSportDivision(season_sport_id=association.id, name="Senior", gender_policy="ANY",
                                         minimum_roster_size=5, maximum_roster_size=15)
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
        game_id = game["id"]

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
