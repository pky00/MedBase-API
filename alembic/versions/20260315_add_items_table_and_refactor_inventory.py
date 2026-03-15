"""add items table and refactor inventory to use item_id FK

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('item_type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # 2. Populate items table from existing medicines, equipment, medical_devices
    conn = op.get_bind()

    # Insert items from medicines
    conn.execute(sa.text("""
        INSERT INTO items (item_type, name, is_deleted, created_by, created_at, updated_by, updated_at)
        SELECT 'medicine', name, is_deleted, created_by, created_at, updated_by, updated_at
        FROM medicines
    """))

    # Insert items from equipment
    conn.execute(sa.text("""
        INSERT INTO items (item_type, name, is_deleted, created_by, created_at, updated_by, updated_at)
        SELECT 'equipment', name, is_deleted, created_by, created_at, updated_by, updated_at
        FROM equipment
    """))

    # Insert items from medical_devices
    conn.execute(sa.text("""
        INSERT INTO items (item_type, name, is_deleted, created_by, created_at, updated_by, updated_at)
        SELECT 'medical_device', name, is_deleted, created_by, created_at, updated_by, updated_at
        FROM medical_devices
    """))

    # 3. Add item_id column to medicines, equipment, medical_devices (nullable first)
    op.add_column('medicines', sa.Column('item_id', sa.Integer(), nullable=True))
    op.add_column('equipment', sa.Column('item_id', sa.Integer(), nullable=True))
    op.add_column('medical_devices', sa.Column('item_id', sa.Integer(), nullable=True))

    # 4. Populate item_id by matching names
    conn.execute(sa.text("""
        UPDATE medicines SET item_id = items.id
        FROM items WHERE items.name = medicines.name AND items.item_type = 'medicine'
    """))
    conn.execute(sa.text("""
        UPDATE equipment SET item_id = items.id
        FROM items WHERE items.name = equipment.name AND items.item_type = 'equipment'
    """))
    conn.execute(sa.text("""
        UPDATE medical_devices SET item_id = items.id
        FROM items WHERE items.name = medical_devices.name AND items.item_type = 'medical_device'
    """))

    # 5. Make item_id non-nullable and add FK + unique constraints
    op.alter_column('medicines', 'item_id', nullable=False)
    op.create_foreign_key('fk_medicines_item_id', 'medicines', 'items', ['item_id'], ['id'])
    op.create_unique_constraint('uq_medicines_item_id', 'medicines', ['item_id'])

    op.alter_column('equipment', 'item_id', nullable=False)
    op.create_foreign_key('fk_equipment_item_id', 'equipment', 'items', ['item_id'], ['id'])
    op.create_unique_constraint('uq_equipment_item_id', 'equipment', ['item_id'])

    op.alter_column('medical_devices', 'item_id', nullable=False)
    op.create_foreign_key('fk_medical_devices_item_id', 'medical_devices', 'items', ['item_id'], ['id'])
    op.create_unique_constraint('uq_medical_devices_item_id', 'medical_devices', ['item_id'])

    # 6. Refactor inventory table: add new item_id FK, migrate data, drop old columns
    # Add new item_id column (nullable first)
    op.add_column('inventory', sa.Column('new_item_id', sa.Integer(), nullable=True))

    # Populate new_item_id based on old item_type + item_id
    conn.execute(sa.text("""
        UPDATE inventory SET new_item_id = m.item_id
        FROM medicines m WHERE inventory.item_type = 'medicine' AND inventory.item_id = m.id
    """))
    conn.execute(sa.text("""
        UPDATE inventory SET new_item_id = e.item_id
        FROM equipment e WHERE inventory.item_type = 'equipment' AND inventory.item_id = e.id
    """))
    conn.execute(sa.text("""
        UPDATE inventory SET new_item_id = md.item_id
        FROM medical_devices md WHERE inventory.item_type = 'medical_device' AND inventory.item_id = md.id
    """))

    # Drop old columns and rename
    op.drop_column('inventory', 'item_type')
    op.drop_column('inventory', 'item_id')
    op.alter_column('inventory', 'new_item_id', new_column_name='item_id', nullable=False)
    op.create_foreign_key('fk_inventory_item_id', 'inventory', 'items', ['item_id'], ['id'])
    op.create_unique_constraint('uq_inventory_item_id', 'inventory', ['item_id'])

    # 7. Refactor inventory_transaction_items: add new item_id FK, migrate data, drop old columns
    op.add_column('inventory_transaction_items', sa.Column('new_item_id', sa.Integer(), nullable=True))

    conn.execute(sa.text("""
        UPDATE inventory_transaction_items SET new_item_id = m.item_id
        FROM medicines m WHERE inventory_transaction_items.item_type = 'medicine' AND inventory_transaction_items.item_id = m.id
    """))
    conn.execute(sa.text("""
        UPDATE inventory_transaction_items SET new_item_id = e.item_id
        FROM equipment e WHERE inventory_transaction_items.item_type = 'equipment' AND inventory_transaction_items.item_id = e.id
    """))
    conn.execute(sa.text("""
        UPDATE inventory_transaction_items SET new_item_id = md.item_id
        FROM medical_devices md WHERE inventory_transaction_items.item_type = 'medical_device' AND inventory_transaction_items.item_id = md.id
    """))

    op.drop_column('inventory_transaction_items', 'item_type')
    op.drop_column('inventory_transaction_items', 'item_id')
    op.alter_column('inventory_transaction_items', 'new_item_id', new_column_name='item_id', nullable=False)
    op.create_foreign_key('fk_inv_tx_items_item_id', 'inventory_transaction_items', 'items', ['item_id'], ['id'])


def downgrade() -> None:
    # Reverse inventory_transaction_items
    op.add_column('inventory_transaction_items', sa.Column('old_item_type', sa.String(), nullable=True))
    op.add_column('inventory_transaction_items', sa.Column('old_item_id', sa.Integer(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE inventory_transaction_items iti SET old_item_type = i.item_type, old_item_id = COALESCE(
            (SELECT m.id FROM medicines m WHERE m.item_id = iti.item_id),
            (SELECT e.id FROM equipment e WHERE e.item_id = iti.item_id),
            (SELECT md.id FROM medical_devices md WHERE md.item_id = iti.item_id)
        )
        FROM items i WHERE i.id = iti.item_id
    """))

    op.drop_constraint('fk_inv_tx_items_item_id', 'inventory_transaction_items', type_='foreignkey')
    op.drop_column('inventory_transaction_items', 'item_id')
    op.alter_column('inventory_transaction_items', 'old_item_type', new_column_name='item_type', nullable=False)
    op.alter_column('inventory_transaction_items', 'old_item_id', new_column_name='item_id', nullable=False)

    # Reverse inventory
    op.add_column('inventory', sa.Column('old_item_type', sa.String(), nullable=True))
    op.add_column('inventory', sa.Column('old_item_id', sa.Integer(), nullable=True))

    conn.execute(sa.text("""
        UPDATE inventory inv SET old_item_type = i.item_type, old_item_id = COALESCE(
            (SELECT m.id FROM medicines m WHERE m.item_id = inv.item_id),
            (SELECT e.id FROM equipment e WHERE e.item_id = inv.item_id),
            (SELECT md.id FROM medical_devices md WHERE md.item_id = inv.item_id)
        )
        FROM items i WHERE i.id = inv.item_id
    """))

    op.drop_constraint('uq_inventory_item_id', 'inventory', type_='unique')
    op.drop_constraint('fk_inventory_item_id', 'inventory', type_='foreignkey')
    op.drop_column('inventory', 'item_id')
    op.alter_column('inventory', 'old_item_type', new_column_name='item_type', nullable=False)
    op.alter_column('inventory', 'old_item_id', new_column_name='item_id', nullable=False)

    # Remove item_id from entity tables
    op.drop_constraint('uq_medical_devices_item_id', 'medical_devices', type_='unique')
    op.drop_constraint('fk_medical_devices_item_id', 'medical_devices', type_='foreignkey')
    op.drop_column('medical_devices', 'item_id')

    op.drop_constraint('uq_equipment_item_id', 'equipment', type_='unique')
    op.drop_constraint('fk_equipment_item_id', 'equipment', type_='foreignkey')
    op.drop_column('equipment', 'item_id')

    op.drop_constraint('uq_medicines_item_id', 'medicines', type_='unique')
    op.drop_constraint('fk_medicines_item_id', 'medicines', type_='foreignkey')
    op.drop_column('medicines', 'item_id')

    # Drop items table
    op.drop_table('items')
