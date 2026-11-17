"""Add game results and reopening history.

Revision ID: f5a6b7c8d901
Revises: e4f5a1b29c70
"""
from alembic import op
import sqlalchemy as sa

revision = "f5a6b7c8d901"
down_revision = "e4f5a1b29c70"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("result_status", sa.String(20), nullable=False, server_default="SCHEDULED"))
    op.add_column("games", sa.Column("home_score", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("away_score", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("finalized_at", sa.DateTime(), nullable=True))
    with op.batch_alter_table("games") as batch:
        batch.add_column(sa.Column("finalized_by", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_games_finalized_by_users", "users", ["finalized_by"], ["id"])
    op.create_table(
        "game_result_reopenings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reopened_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reopened_at", sa.DateTime(), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=False),
        sa.Column("away_score", sa.Integer(), nullable=False),
        sa.Column("finalized_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("finalized_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_game_result_reopenings_game_id", "game_result_reopenings", ["game_id"])


def downgrade():
    raise RuntimeError("Game results and correction history would be lost; restore the pre-migration backup instead.")
