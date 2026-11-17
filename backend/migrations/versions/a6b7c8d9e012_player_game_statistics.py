"""Add configurable sport statistics and game participation.

Revision ID: a6b7c8d9e012
Revises: f5a6b7c8d901
"""
from alembic import op
import sqlalchemy as sa

revision = "a6b7c8d9e012"
down_revision = "f5a6b7c8d901"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sport_statistic_configurations",
        sa.Column("season_sport_id", sa.Integer(), sa.ForeignKey("season_sports.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("allow_team_points", sa.Boolean(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "statistic_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("season_sport_id", sa.Integer(),
                  sa.ForeignKey("sport_statistic_configurations.season_sport_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("abbreviation", sa.String(20), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("is_scoring", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("season_sport_id", "name", name="uq_statistic_type_sport_name"),
        sa.UniqueConstraint("season_sport_id", "abbreviation", name="uq_statistic_type_sport_abbreviation"),
    )
    op.create_table(
        "game_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("season_teams.id"), nullable=False),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.UniqueConstraint("game_id", "player_id", name="uq_game_participant_player"),
    )
    op.create_index("ix_game_participants_game_id", "game_participants", ["game_id"])
    op.create_table(
        "player_game_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("game_participants.id"), nullable=False),
        sa.Column("statistic_type_id", sa.Integer(), sa.ForeignKey("statistic_types.id"), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("participant_id", "statistic_type_id", name="uq_participant_statistic_type"),
    )
    op.create_table(
        "game_team_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("season_teams.id"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.UniqueConstraint("game_id", "team_id", name="uq_game_team_points"),
    )


def downgrade():
    raise RuntimeError("Player statistics would be lost; restore the pre-migration backup instead.")
