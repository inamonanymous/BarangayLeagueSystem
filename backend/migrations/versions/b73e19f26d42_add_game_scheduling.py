"""add game scheduling

Revision ID: b73e19f26d42
Revises: a6b93c1d5e80
"""
from alembic import op
import sqlalchemy as sa


revision = "b73e19f26d42"
down_revision = "a6b93c1d5e80"
branch_labels = None
depends_on = None


def upgrade():
    lock = op.create_table(
        "schedule_lock",
        sa.Column("id", sa.Integer(), primary_key=True),
    )
    op.bulk_insert(lock, [{"id": 1}])
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("season_sport_division_id", sa.Integer(), sa.ForeignKey("season_sport_divisions.id"), nullable=False),
        sa.Column("home_team_id", sa.Integer(), sa.ForeignKey("season_teams.id"), nullable=False),
        sa.Column("away_team_id", sa.Integer(), sa.ForeignKey("season_teams.id"), nullable=False),
        sa.Column("venue", sa.String(150), nullable=False),
        sa.Column("venue_key", sa.String(150), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_games_season_sport_division_id", "games", ["season_sport_division_id"])
    op.create_index("ix_games_starts_at", "games", ["starts_at"])


def downgrade():
    op.drop_table("games")
    op.drop_table("schedule_lock")
