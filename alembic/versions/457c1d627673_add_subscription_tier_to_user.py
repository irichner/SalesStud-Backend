"""add_subscription_tier_to_user

Revision ID: 457c1d627673
Revises: 06913d0e19f2
Create Date: 2026-02-26 21:14:13.681784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '457c1d627673'
down_revision: Union[str, Sequence[str], None] = '06913d0e19f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Users', sa.Column('subscription_tier', sa.String(length=20), nullable=True, default='starter'))


def downgrade() -> None:
    """Downgrade schema."""
    pass
