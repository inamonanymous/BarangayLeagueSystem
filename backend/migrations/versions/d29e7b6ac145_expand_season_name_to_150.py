"""expand season name to 150 characters

Revision ID: d29e7b6ac145
Revises: c8d47a1e2f90
Create Date: 2026-11-12

"""
from alembic import op
import sqlalchemy as sa


revision = "d29e7b6ac145"
down_revision = "c8d47a1e2f90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("seasons") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=100),
            type_=sa.String(length=150),
            existing_nullable=False,
        )


def downgrade():
    connection = op.get_bind()
    long_names = connection.execute(
        sa.text("SELECT COUNT(*) FROM seasons WHERE CHAR_LENGTH(name) > 100")
    ).scalar_one()
    if long_names:
        raise RuntimeError(
            "Cannot shrink season names while any name exceeds 100 characters."
        )

    with op.batch_alter_table("seasons") as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=150),
            type_=sa.String(length=100),
            existing_nullable=False,
        )
