"""add phase 2 execution metadata and error details to analysis_run

Revision ID: c5d264271c36
Revises: 76dae4d80cde
Create Date: 2026-08-17 06:37:49.030459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5d264271c36'
down_revision: Union[str, Sequence[str], None] = '76dae4d80cde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'analysis_run',
        sa.Column('execution_metadata', sa.JSON(), nullable=True),
    )
    op.add_column(
        'analysis_run',
        sa.Column('error_type', sa.String(length=100), nullable=True),
    )
    op.add_column(
        'analysis_run',
        sa.Column('error_details', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('analysis_run', 'error_details')
    op.drop_column('analysis_run', 'error_type')
    op.drop_column('analysis_run', 'execution_metadata')

