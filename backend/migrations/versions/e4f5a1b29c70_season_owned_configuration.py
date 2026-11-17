"""Move sport and division settings to their season-owned assignments.

Revision ID: e4f5a1b29c70
Revises: b73e19f26d42
"""
from alembic import op
import sqlalchemy as sa


revision = "e4f5a1b29c70"
down_revision = "b73e19f26d42"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "sqlite" and connection.execute(sa.text("PRAGMA foreign_keys")).scalar_one():
        raise RuntimeError(
            "SQLite foreign keys must be disabled before starting this migration; "
            "back up the database and verify foreign_key_check afterward."
        )
    checks = (
        ("SELECT COUNT(*) FROM season_sports ss LEFT JOIN sports s ON s.id = ss.sport_id "
         "WHERE s.id IS NULL", "season sports reference missing sports"),
        ("SELECT COUNT(*) FROM season_sport_divisions sd LEFT JOIN divisions d ON d.id = sd.division_id "
         "WHERE d.id IS NULL", "season divisions reference missing divisions"),
        ("SELECT COUNT(*) FROM (SELECT ss.season_id, LOWER(s.name) FROM season_sports ss "
         "JOIN sports s ON s.id = ss.sport_id GROUP BY ss.season_id, LOWER(s.name) "
         "HAVING COUNT(*) > 1) duplicates", "duplicate sport names in a season"),
        ("SELECT COUNT(*) FROM (SELECT sd.season_sport_id, LOWER(d.name) FROM season_sport_divisions sd "
         "JOIN divisions d ON d.id = sd.division_id GROUP BY sd.season_sport_id, LOWER(d.name) "
         "HAVING COUNT(*) > 1) duplicates", "duplicate division names in a season sport"),
    )
    for sql, problem in checks:
        if connection.execute(sa.text(sql)).scalar_one():
            raise RuntimeError(f"Cannot migrate season configuration: {problem}.")

    with op.batch_alter_table("season_sports") as batch:
        batch.add_column(sa.Column("name", sa.String(100), nullable=True))
        batch.add_column(sa.Column("description", sa.Text(), nullable=True))
    with op.batch_alter_table("season_sport_divisions") as batch:
        batch.add_column(sa.Column("name", sa.String(100), nullable=True))
        batch.add_column(sa.Column("gender_policy", sa.String(20), nullable=True))
        batch.add_column(sa.Column("minimum_roster_size", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("maximum_roster_size", sa.Integer(), nullable=True))
    connection.execute(sa.text(
        "UPDATE season_sports SET name = (SELECT name FROM sports WHERE sports.id = season_sports.sport_id), "
        "description = (SELECT description FROM sports WHERE sports.id = season_sports.sport_id)"
    ))
    connection.execute(sa.text(
        "UPDATE season_sport_divisions SET "
        "name = (SELECT name FROM divisions WHERE divisions.id = season_sport_divisions.division_id), "
        "gender_policy = (SELECT gender_policy FROM divisions WHERE divisions.id = season_sport_divisions.division_id), "
        "minimum_roster_size = (SELECT minimum_roster_size FROM divisions WHERE divisions.id = season_sport_divisions.division_id), "
        "maximum_roster_size = (SELECT maximum_roster_size FROM divisions WHERE divisions.id = season_sport_divisions.division_id)"
    ))
    # MySQL uses the old composite indexes to support the parent foreign keys.
    # Create their replacements before dropping the old unique constraints.
    op.create_index("ix_season_sports_season_id_migration", "season_sports", ["season_id"])
    op.create_index(
        "ix_season_sport_divisions_season_sport_id_migration",
        "season_sport_divisions",
        ["season_sport_id"],
    )
    with op.batch_alter_table("season_sport_divisions") as batch:
        batch.drop_constraint("fk_season_sport_divisions_division_id_divisions", type_="foreignkey")
        batch.drop_constraint("uq_season_sport_division", type_="unique")
        batch.drop_column("division_id")
        batch.alter_column("name", existing_type=sa.String(100), nullable=False)
        batch.alter_column("gender_policy", existing_type=sa.String(20), nullable=False)
        batch.alter_column("minimum_roster_size", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("maximum_roster_size", existing_type=sa.Integer(), nullable=False)
        batch.create_unique_constraint("uq_season_sport_division_name", ["season_sport_id", "name"])
    with op.batch_alter_table("season_sports") as batch:
        batch.drop_constraint("fk_season_sports_sport_id_sports", type_="foreignkey")
        batch.drop_constraint("uq_season_sport", type_="unique")
        batch.drop_column("sport_id")
        batch.alter_column("name", existing_type=sa.String(100), nullable=False)
        batch.create_unique_constraint("uq_season_sport_name", ["season_id", "name"])
    op.drop_index("ix_season_sport_divisions_season_sport_id_migration", table_name="season_sport_divisions")
    op.drop_index("ix_season_sports_season_id_migration", table_name="season_sports")
    op.drop_table("divisions")
    op.drop_table("sports")


def downgrade():
    raise RuntimeError("Season configuration may have diverged; restore the pre-migration backup instead.")
