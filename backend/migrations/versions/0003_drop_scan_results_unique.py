"""drop unique constraint on scan_results (file_id, check_name)

Revision ID: 0003_drop_scan_results_unique
Revises: 0002_add_cascade_fk
Create Date: 2026-07-12 00:00:00.000000

"""

from alembic import op

revision = "0003_drop_scan_results_unique"
down_revision = "0002_add_cascade_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_scan_result_file_check",
        "scan_results",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_scan_result_file_check",
        "scan_results",
        ["file_id", "check_name"],
    )
