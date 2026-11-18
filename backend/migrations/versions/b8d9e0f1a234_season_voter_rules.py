"""Add season voter rules and year-specific player voter IDs.

Revision ID: b8d9e0f1a234
Revises: a6b7c8d9e012
"""
from alembic import op
import sqlalchemy as sa

revision = "b8d9e0f1a234"
down_revision = "a6b7c8d9e012"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("seasons") as batch:
        batch.add_column(sa.Column("voter_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "player_voter_ids",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("voter_number", sa.String(100), nullable=False),
        sa.Column("normalized_number", sa.String(200), nullable=False),
        sa.UniqueConstraint("player_id", "year", name="uq_player_voter_id_year"),
        sa.UniqueConstraint("year", "normalized_number", name="uq_voter_id_year_number"),
    )


def downgrade():
    raise RuntimeError("Voter IDs would be lost; restore the pre-migration backup instead.")
