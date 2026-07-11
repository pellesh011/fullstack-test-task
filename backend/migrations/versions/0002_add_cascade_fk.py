"""add cascade foreign keys and unique constraint on scan_results

Revision ID: 0002_add_cascade_fk
Revises: 7f3a1e2b4c5d
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_cascade_fk"
down_revision: Union[str, Sequence[str], None] = "4a2f1c1e1e4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing foreign keys
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.drop_constraint("scan_results_file_id_fkey", "scan_results", type_="foreignkey")

    # Add new foreign keys with CASCADE
    op.create_foreign_key(
        "alerts_file_id_fkey", "alerts", "files", ["file_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "scan_results_file_id_fkey",
        "scan_results",
        "files",
        ["file_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add unique constraint on scan_results (file_id, check_name)
    op.create_unique_constraint(
        "uq_scan_result_file_check", "scan_results", ["file_id", "check_name"]
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint("uq_scan_result_file_check", "scan_results", type_="unique")

    # Drop CASCADE foreign keys
    op.drop_constraint("alerts_file_id_fkey", "alerts", type_="foreignkey")
    op.drop_constraint("scan_results_file_id_fkey", "scan_results", type_="foreignkey")

    # Restore original foreign keys without CASCADE
    op.create_foreign_key(
        "alerts_file_id_fkey", "alerts", "files", ["file_id"], ["id"]
    )
    op.create_foreign_key(
        "scan_results_file_id_fkey", "scan_results", "files", ["file_id"], ["id"]
    )