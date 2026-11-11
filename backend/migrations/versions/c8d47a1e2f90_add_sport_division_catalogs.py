"""add sport, division, and season association tables

Revision ID: c8d47a1e2f90
Revises: a41c9d2e7b6f
Create Date: 2026-11-11

"""
from alembic import op
import sqlalchemy as sa


revision = "c8d47a1e2f90"
down_revision = "a41c9d2e7b6f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_sports_name"),
    )
    op.create_table(
        "divisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "gender_policy",
            sa.Enum("ANY", "MALE_ONLY", "FEMALE_ONLY", "MIXED", name="gender_policy"),
            nullable=False,
            server_default="ANY",
        ),
        sa.Column("minimum_roster_size", sa.Integer(), nullable=False),
        sa.Column("maximum_roster_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_divisions_name"),
    )
    op.create_table(
        "season_sports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("sport_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"], name="fk_season_sports_season_id_seasons"),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"], name="fk_season_sports_sport_id_sports"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_id", "sport_id", name="uq_season_sport"),
    )
    op.create_table(
        "season_sport_divisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_sport_id", sa.Integer(), nullable=False),
        sa.Column("division_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(
            ["season_sport_id"],
            ["season_sports.id"],
            name="fk_season_sport_divisions_season_sport_id_season_sports",
        ),
        sa.ForeignKeyConstraint(
            ["division_id"],
            ["divisions.id"],
            name="fk_season_sport_divisions_division_id_divisions",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("season_sport_id", "division_id", name="uq_season_sport_division"),
    )


def downgrade():
    op.drop_table("season_sport_divisions")
    op.drop_table("season_sports")
    op.drop_table("divisions")
    op.drop_table("sports")