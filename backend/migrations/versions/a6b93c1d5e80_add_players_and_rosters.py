"""add players, rosters, eligibility, and team archive fields

Revision ID: a6b93c1d5e80
Revises: f2c8a93d61b4
Create Date: 2026-11-12

"""
from alembic import op
import sqlalchemy as sa


revision = "a6b93c1d5e80"
down_revision = "f2c8a93d61b4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("season_teams") as batch_op:
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("archived_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_season_teams_archived_by_users",
            "users",
            ["archived_by"],
            ["id"],
        )

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("middle_name", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("archived_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["archived_by"], ["users.id"], name="fk_players_archived_by_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "first_name",
            "middle_name",
            "last_name",
            "birthdate",
            name="uq_player_identity",
        ),
    )
    op.create_table(
        "rosters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("jersey_number", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["season_team_id"], ["season_teams.id"], name="fk_rosters_season_team_id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_rosters_player_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_team_id", "jersey_number", name="uq_roster_team_jersey"),
        sa.UniqueConstraint("season_team_id", "player_id", name="uq_roster_team_player"),
    )
    op.create_table(
        "season_player_eligibilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("is_voter_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("voter_number", sa.String(length=100), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], name="fk_eligibilities_season_id"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_eligibilities_player_id"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], name="fk_eligibilities_verified_by"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_id", "player_id", name="uq_season_player_eligibility"),
    )


def downgrade():
    op.drop_table("season_player_eligibilities")
    op.drop_table("rosters")
    op.drop_table("players")
    with op.batch_alter_table("season_teams") as batch_op:
        batch_op.drop_constraint("fk_season_teams_archived_by_users", type_="foreignkey")
        batch_op.drop_column("archived_by")
        batch_op.drop_column("archived_at")
        batch_op.drop_column("is_archived")
