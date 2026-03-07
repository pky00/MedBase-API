"""remove type column from third_parties

Revision ID: a1b2c3d4e5f6
Revises: 9c4ca3ae2e81
Create Date: 2026-03-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9c4ca3ae2e81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('third_parties', 'type')


def downgrade() -> None:
    op.add_column('third_parties', sa.Column('type', sa.String(), nullable=True))
