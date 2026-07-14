"""add odometer constraints on vehicle_assignments

Revision ID: 73364f3ac51a
Revises: 3a377ccf5d4f
Create Date: 2026-07-14 12:44:28.804663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73364f3ac51a'
down_revision: Union[str, Sequence[str], None] = '3a377ccf5d4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_vehicle_assignments_odometer_only_for_drivers",
        "vehicle_assignments",
        "assignment_type = 'DRIVER' OR "
            "(odometer_out_km IS NULL AND odometer_in_km IS NULL)",
    )
    op.create_check_constraint(
        "ck_vehicle_assignments_odometer_out_not_null_for_drivers",
        "vehicle_assignments",
        "assignment_type <> 'DRIVER'"
            "OR odometer_out_km IS NOT NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_vehicle_assignments_odometer_only_for_drivers",
        "vehicle_assignments",
        type_="check",
    )
    op.drop_constraint(
        "ck_vehicle_assignments_odometer_out_not_null_for_drivers",
        "vehicle_assignments",
        type_="check",
    )
