"""add code fields and inventory_transaction appointment_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-10 00:00:00.000000

"""
import secrets
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Unambiguous characters: no 0/O, 1/I/L
_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(6))


def _add_code_column(table_name: str, constraint_name: str) -> None:
    """Add a code column, backfill existing rows, then make non-nullable + unique."""
    op.add_column(table_name, sa.Column('code', sa.String(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text(f"SELECT id FROM {table_name}")).fetchall()
    used_codes = set()
    for row in rows:
        code = _generate_code()
        while code in used_codes:
            code = _generate_code()
        used_codes.add(code)
        conn.execute(
            sa.text(f"UPDATE {table_name} SET code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    op.alter_column(table_name, 'code', nullable=False)
    op.create_unique_constraint(constraint_name, table_name, ['code'])


def upgrade() -> None:
    # Add code columns to all tables
    _add_code_column('third_parties', 'uq_third_parties_code')
    _add_code_column('appointments', 'uq_appointments_code')
    _add_code_column('medicines', 'uq_medicines_code')
    _add_code_column('equipment', 'uq_equipment_code')
    _add_code_column('medical_devices', 'uq_medical_devices_code')

    # Add appointment_id column to inventory_transactions
    op.add_column('inventory_transactions', sa.Column('appointment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_inventory_transactions_appointment_id',
        'inventory_transactions', 'appointments',
        ['appointment_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_inventory_transactions_appointment_id', 'inventory_transactions', type_='foreignkey')
    op.drop_column('inventory_transactions', 'appointment_id')

    for table, constraint in [
        ('medical_devices', 'uq_medical_devices_code'),
        ('equipment', 'uq_equipment_code'),
        ('medicines', 'uq_medicines_code'),
        ('appointments', 'uq_appointments_code'),
        ('third_parties', 'uq_third_parties_code'),
    ]:
        op.drop_constraint(constraint, table, type_='unique')
        op.drop_column(table, 'code')
