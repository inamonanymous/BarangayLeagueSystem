import importlib

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


@pytest.mark.parametrize("foreign_keys_enabled", [False, True])
def test_migration_copies_settings_and_preserves_assignment_links(foreign_keys_enabled):
    catalog = importlib.import_module("migrations.versions.c8d47a1e2f90_add_sport_division_catalogs")
    migration = importlib.import_module("migrations.versions.e4f5a1b29c70_season_owned_configuration")
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        if foreign_keys_enabled:
            connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text("CREATE TABLE seasons (id INTEGER PRIMARY KEY)"))
        with Operations.context(MigrationContext.configure(connection)):
            catalog.upgrade()
        connection.execute(text("INSERT INTO seasons (id) VALUES (1), (2)"))
        connection.execute(text("INSERT INTO sports (id, name, description) VALUES (1, 'Basketball', 'Court'), (2, 'Unused', NULL)"))
        connection.execute(text("INSERT INTO divisions (id, name, gender_policy, minimum_roster_size, maximum_roster_size) VALUES (1, 'Senior', 'ANY', 5, 15), (2, 'Unused', 'ANY', 1, 10)"))
        connection.execute(text("INSERT INTO season_sports (id, season_id, sport_id) VALUES (10, 1, 1), (20, 2, 1)"))
        connection.execute(text("INSERT INTO season_sport_divisions (id, season_sport_id, division_id) VALUES (100, 10, 1), (200, 20, 1)"))
        connection.execute(text("CREATE TABLE season_teams (id INTEGER PRIMARY KEY, season_sport_division_id INTEGER REFERENCES season_sport_divisions(id))"))
        connection.execute(text("CREATE TABLE rosters (id INTEGER PRIMARY KEY, season_team_id INTEGER REFERENCES season_teams(id), player_id INTEGER)"))
        connection.execute(text("CREATE TABLE games (id INTEGER PRIMARY KEY, season_sport_division_id INTEGER REFERENCES season_sport_divisions(id), home_team_id INTEGER REFERENCES season_teams(id))"))
        connection.execute(text("INSERT INTO season_teams VALUES (1000, 100), (2000, 200)"))
        connection.execute(text("INSERT INTO rosters VALUES (1, 1000, 7), (2, 2000, 7)"))
        connection.execute(text("INSERT INTO games VALUES (1, 100, 1000), (2, 200, 2000)"))
        with Operations.context(MigrationContext.configure(connection)):
            if foreign_keys_enabled:
                with pytest.raises(RuntimeError, match="foreign keys must be disabled"):
                    migration.upgrade()
                assert "sport_id" in [column["name"] for column in inspect(connection).get_columns("season_sports")]
                assert connection.execute(text("SELECT COUNT(*) FROM season_teams")).scalar_one() == 2
                return
            migration.upgrade()
        assert connection.execute(text("SELECT id, season_id, name, description FROM season_sports ORDER BY id")).all() == [
            (10, 1, "Basketball", "Court"), (20, 2, "Basketball", "Court"),
        ]
        assert connection.execute(text("SELECT id, season_sport_id, name, minimum_roster_size, maximum_roster_size FROM season_sport_divisions ORDER BY id")).all() == [
            (100, 10, "Senior", 5, 15), (200, 20, "Senior", 5, 15),
        ]
        assert connection.execute(text("SELECT COUNT(*) FROM season_teams t JOIN season_sport_divisions d ON d.id = t.season_sport_division_id JOIN games g ON g.season_sport_division_id = d.id AND g.home_team_id = t.id JOIN rosters r ON r.season_team_id = t.id")).scalar_one() == 2
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []
        assert "sports" not in inspect(connection).get_table_names()
        assert "divisions" not in inspect(connection).get_table_names()
        connection.execute(text("UPDATE season_sport_divisions SET maximum_roster_size = 12 WHERE id = 100"))
        assert connection.execute(text("SELECT maximum_roster_size FROM season_sport_divisions WHERE id = 200")).scalar_one() == 15
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            migration.downgrade()
    engine.dispose()


@pytest.mark.parametrize(
    ("invalid_sql", "message"),
    [
        ("INSERT INTO season_sports (season_id, sport_id) VALUES (1, 999)", "missing sports"),
        ("INSERT INTO season_sport_divisions (season_sport_id, division_id) VALUES (1, 999)", "missing divisions"),
        ("INSERT INTO season_sports (season_id, sport_id) VALUES (1, 2)", "duplicate sport names"),
        ("INSERT INTO season_sport_divisions (season_sport_id, division_id) VALUES (1, 2)", "duplicate division names"),
    ],
)
def test_invalid_legacy_data_is_rejected_before_schema_changes(invalid_sql, message):
    catalog = importlib.import_module("migrations.versions.c8d47a1e2f90_add_sport_division_catalogs")
    migration = importlib.import_module("migrations.versions.e4f5a1b29c70_season_owned_configuration")
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE seasons (id INTEGER PRIMARY KEY)"))
        with Operations.context(MigrationContext.configure(connection)):
            catalog.upgrade()
        connection.execute(text("INSERT INTO seasons (id) VALUES (1)"))
        connection.execute(text("INSERT INTO sports (id, name) VALUES (1, 'Basketball'), (2, 'BASKETBALL')"))
        connection.execute(text("INSERT INTO divisions (id, name, minimum_roster_size, maximum_roster_size) VALUES (1, 'Senior', 5, 15), (2, 'SENIOR', 5, 15)"))
        connection.execute(text("INSERT INTO season_sports (id, season_id, sport_id) VALUES (1, 1, 1)"))
        connection.execute(text("INSERT INTO season_sport_divisions (season_sport_id, division_id) VALUES (1, 1)"))
        connection.execute(text(invalid_sql))
        with Operations.context(MigrationContext.configure(connection)):
            with pytest.raises(RuntimeError, match=message):
                migration.upgrade()
        assert "sport_id" in [column["name"] for column in inspect(connection).get_columns("season_sports")]
        assert "division_id" in [column["name"] for column in inspect(connection).get_columns("season_sport_divisions")]
        assert {"sports", "divisions"}.issubset(inspect(connection).get_table_names())
    engine.dispose()
