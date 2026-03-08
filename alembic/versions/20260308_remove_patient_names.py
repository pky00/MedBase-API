"""remove first_name and last_name from patients

Revision ID: a1b2c3d4e5f6
Revises: 7e69c2d87fc9
Create Date: 2026-03-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7e69c2d87fc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('patients', 'first_name')
    op.drop_column('patients', 'last_name')


def downgrade() -> None:
    op.add_column('patients', sa.Column('last_name', sa.String(), nullable=False, server_default=''))
    op.add_column('patients', sa.Column('first_name', sa.String(), nullable=False, server_default=''))
