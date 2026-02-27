"""add_schema_proposal_table

Revision ID: 06913d0e19f2
Revises: 04b4b878a896
Create Date: 2026-02-26 21:13:16.290473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06913d0e19f2'
down_revision: Union[str, Sequence[str], None] = '04b4b878a896'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('SchemaProposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('desired_change', sa.Text(), nullable=False),
        sa.Column('proposal_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['Users.UserID']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['Users.UserID']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('SchemaProposals')
