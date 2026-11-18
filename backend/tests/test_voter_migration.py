import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def test_voter_migration_preserves_existing_eligibility_and_defaults_non_strict():
    path = Path(__file__).parents[1] / "migrations" / "versions" / "b8d9e0f1a234_season_voter_rules.py"
    spec = importlib.util.spec_from_file_location("voter_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE seasons (id INTEGER PRIMARY KEY, year INTEGER NOT NULL)"))
        connection.execute(text("CREATE TABLE players (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE season_player_eligibilities (id INTEGER PRIMARY KEY, voter_number VARCHAR(100))"))
        connection.execute(text("INSERT INTO seasons (id, year) VALUES (1, 2026)"))
        connection.execute(text("INSERT INTO season_player_eligibilities (id, voter_number) VALUES (1, 'OLD-ID')"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert connection.execute(text("SELECT voter_required FROM seasons WHERE id = 1")).scalar_one() == 0
        assert connection.execute(text("SELECT voter_number FROM season_player_eligibilities WHERE id = 1")).scalar_one() == "OLD-ID"
        assert connection.execute(text("SELECT COUNT(*) FROM player_voter_ids")).scalar_one() == 0
        constraints = inspect(connection).get_unique_constraints("player_voter_ids")
        assert {tuple(item["column_names"]) for item in constraints} == {
            ("player_id", "year"), ("year", "normalized_number"),
        }
