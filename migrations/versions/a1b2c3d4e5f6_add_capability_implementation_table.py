"""add_capability_implementation_table_and_drop_implementation_key

Revision ID: a1b2c3d4e5f6
Revises: 9141edf7efd4
Create Date: 2026-08-18 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9141edf7efd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'capability_implementation',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scientific_capability_id', sa.Integer(), nullable=False),
        sa.Column('implementation_key', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False, server_default='core_engine'),
        sa.Column('adapter_module', sa.String(length=255), nullable=True),
        sa.Column('backend_environment', sa.String(length=100), nullable=False, server_default='local_host'),
        sa.Column('runtime_version', sa.String(length=64), nullable=True),
        sa.Column('availability', sa.String(length=32), nullable=False, server_default='installed'),
        sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='known'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('execution_parameters', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['scientific_capability_id'], ['scientific_capability.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_capability_implementation_implementation_key'), 'capability_implementation', ['implementation_key'], unique=True)
    op.create_index(op.f('ix_capability_implementation_scientific_capability_id'), 'capability_implementation', ['scientific_capability_id'], unique=False)
    
    # Drop implementation_key from scientific_capability
    op.drop_column('scientific_capability', 'implementation_key')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('scientific_capability', sa.Column('implementation_key', sa.String(length=100), nullable=True))
    op.drop_index(op.f('ix_capability_implementation_scientific_capability_id'), table_name='capability_implementation')
    op.drop_index(op.f('ix_capability_implementation_implementation_key'), table_name='capability_implementation')
    op.drop_table('capability_implementation')
