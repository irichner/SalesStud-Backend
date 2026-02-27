"""add_agent_memory_and_graph_config

Revision ID: 04b4b878a896
Revises: daa2efc26701
Create Date: 2026-02-26 21:11:37.292237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04b4b878a896'
down_revision: Union[str, Sequence[str], None] = 'daa2efc26701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add graph_config column to AIAgents
    op.add_column('AIAgents', sa.Column('graph_config', sa.JSON(), nullable=True))

    # Create AgentMemory table
    op.create_table('AgentMemory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['AIAgents.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop AgentMemory table
    op.drop_table('AgentMemory')

    # Drop graph_config column from AIAgents
    op.drop_column('AIAgents', 'graph_config')
