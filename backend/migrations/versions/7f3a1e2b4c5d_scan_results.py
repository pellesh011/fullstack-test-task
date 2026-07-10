"""add scan_results table, remove scan_details, size to BigInteger

Revision ID: 7f3a1e2b4c5d
Revises: 0d6439d2e79f
Create Date: 2026-04-03 16:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f3a1e2b4c5d"
down_revision: Union[str, Sequence[str], None] = "0d6439d2e79f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("files", "size", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.drop_column("files", "scan_details")
    op.alter_column(
        "alerts", "message", type_=sa.Text(), existing_type=sa.String(length=500)
    )


def downgrade() -> None:
    op.alter_column(
        "alerts", "message", type_=sa.String(length=500), existing_type=sa.Text()
    )
    op.add_column(
        "files", sa.Column("scan_details", sa.String(length=500), nullable=True)
    )
    op.alter_column("files", "size", type_=sa.Integer(), existing_type=sa.BigInteger())
    op.drop_table("scan_results")
