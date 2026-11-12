"""create season teams

Revision ID: f2c8a93d61b4
Revises: d29e7b6ac145
Create Date: 2026-11-12

"""
from alembic import op
import sqlalchemy as sa


revision = "f2c8a93d61b4"
down_revision = "d29e7b6ac145"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "season_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_sport_division_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("barangay", sa.String(length=150), nullable=False),
        sa.Column("coach_name", sa.String(length=150), nullable=True),
        sa.Column("manager_name", sa.String(length=150), nullable=True),
        sa.Column("team_color", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["season_sport_division_id"],
            ["season_sport_divisions.id"],
            name="fk_season_teams_season_sport_division_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "season_sport_division_id",
            "name",
            name="uq_season_team_division_name",
        ),
    )


def downgrade():
    op.drop_table("season_teams")
