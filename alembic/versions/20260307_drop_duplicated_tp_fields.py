"""drop duplicated third_party fields from entity tables

Revision ID: a1b2c3d4e5f6
Revises: 7146ec59d326
Create Date: 2026-03-07 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7146ec59d326'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraints/indexes first
    op.drop_constraint('doctors_name_key', 'doctors', type_='unique')
    op.drop_constraint('partners_name_key', 'partners', type_='unique')
    op.drop_index(op.f('ix_users_email'), table_name='users')

    # Drop columns from doctors
    op.drop_column('doctors', 'name')
    op.drop_column('doctors', 'phone')
    op.drop_column('doctors', 'email')

    # Drop columns from partners
    op.drop_column('partners', 'name')
    op.drop_column('partners', 'phone')
    op.drop_column('partners', 'email')

    # Drop columns from patients
    op.drop_column('patients', 'phone')
    op.drop_column('patients', 'email')

    # Drop column from users
    op.drop_column('users', 'email')


def downgrade() -> None:
    # Re-add columns to users
    op.add_column('users', sa.Column('email', sa.VARCHAR(), nullable=True))

    # Re-add columns to patients
    op.add_column('patients', sa.Column('email', sa.VARCHAR(), nullable=True))
    op.add_column('patients', sa.Column('phone', sa.VARCHAR(), nullable=True))

    # Re-add columns to partners
    op.add_column('partners', sa.Column('email', sa.VARCHAR(), nullable=True))
    op.add_column('partners', sa.Column('phone', sa.VARCHAR(), nullable=True))
    op.add_column('partners', sa.Column('name', sa.VARCHAR(), nullable=True))

    # Re-add columns to doctors
    op.add_column('doctors', sa.Column('email', sa.VARCHAR(), nullable=True))
    op.add_column('doctors', sa.Column('phone', sa.VARCHAR(), nullable=True))
    op.add_column('doctors', sa.Column('name', sa.VARCHAR(), nullable=True))

    # Re-add unique constraints/indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_unique_constraint('partners_name_key', 'partners', ['name'])
    op.create_unique_constraint('doctors_name_key', 'doctors', ['name'])
