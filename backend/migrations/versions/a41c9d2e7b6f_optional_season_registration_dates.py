"""make season registration dates optional

Revision ID: a41c9d2e7b6f
Revises: f7af23243b84
Create Date: 2026-11-11

"""
from alembic import op
import sqlalchemy as sa


revision = "a41c9d2e7b6f"
down_revision = "f7af23243b84"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("seasons") as batch_op:
        batch_op.alter_column(
            "registration_start_date",
            existing_type=sa.Date(),
            nullable=True,
        )
        batch_op.alter_column(
            "registration_end_date",
            existing_type=sa.Date(),
            nullable=True,
        )


def downgrade():
    connection = op.get_bind()
    missing_registration_dates = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM seasons "
            "WHERE registration_start_date IS NULL "
            "OR registration_end_date IS NULL"
        )
    ).scalar_one()

    if missing_registration_dates:
        raise RuntimeError(
            "Cannot make season registration dates required while seasons "
            "have missing registration dates. Populate them before downgrading."
        )

    with op.batch_alter_table("seasons") as batch_op:
        batch_op.alter_column(
            "registration_start_date",
            existing_type=sa.Date(),
            nullable=False,
        )
        batch_op.alter_column(
            "registration_end_date",
            existing_type=sa.Date(),
            nullable=False,
        )