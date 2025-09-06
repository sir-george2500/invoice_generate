"""Add custom field setup tracking to business model

Revision ID: a0b2f53464be
Revises: b2df0aadab30
Create Date: 2025-09-06 03:25:06.407894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0b2f53464be'
down_revision: Union[str, None] = 'b2df0aadab30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add custom field setup tracking columns to businesses table
    op.add_column('businesses', sa.Column('custom_fields_setup_status', sa.String(50), nullable=True, default='pending'))
    op.add_column('businesses', sa.Column('custom_fields_setup_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('businesses', sa.Column('custom_fields_setup_result', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove custom field setup tracking columns from businesses table
    op.drop_column('businesses', 'custom_fields_setup_result')
    op.drop_column('businesses', 'custom_fields_setup_at')
    op.drop_column('businesses', 'custom_fields_setup_status')
