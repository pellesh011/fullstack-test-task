"""add original_mime_type to files

Revision ID: 0001
Revises:
Create Date: 2026-07-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4a2f1c1e1e4a"
down_revision: Union[str, None] = "7f3a1e2b4c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "files",
        sa.Column("original_mime_type", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("files", "original_mime_type")
