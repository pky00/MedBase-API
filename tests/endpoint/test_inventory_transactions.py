"""Tests for inventory transaction endpoints."""
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.inventory_transaction import InventoryTransaction
from app.model.inventory_transaction_item import InventoryTransactionItem
from app.model.inventory import Inventory
from app.model.medicine import Medicine
from app.model.medicine_category import MedicineCategory
from app.model.equipment import Equipment
from app.model.equipment_category import EquipmentCategory
from app.model.partner import Partner
from app.model.doctor import Doctor
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def medicine_category(db_session: AsyncSession, admin_user: User) -> MedicineCategory:
    """Create a medicine category for testing."""
    cat = MedicineCategory(
        name="Test Category",
        description="For testing",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


@pytest.fixture
async def medicine_with_inventory(
    db_session: AsyncSession, admin_user: User, medicine_category: MedicineCategory,
) -> tuple:
    """Create a medicine with inventory record."""
    medicine = Medicine(
        name="Test Medicine",
        category_id=medicine_category.id,
        unit="tablets",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(medicine)
    await db_session.flush()
    await db_session.refresh(medicine)

    inventory = Inventory(
        item_type="medicine",
        item_id=medicine.id,
        quantity=100,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    return medicine, inventory


@pytest.fixture
async def equipment_with_inventory(
    db_session: AsyncSession, admin_user: User,
) -> tuple:
    """Create equipment with inventory record."""
    cat = EquipmentCategory(
        name="Test Equip Cat",
        description="For testing",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)

    equip = Equipment(
        name="Test Equipment",
        category_id=cat.id,
        condition="new",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(equip)
    await db_session.flush()
    await db_session.refresh(equip)

    inventory = Inventory(
        item_type="equipment",
        item_id=equip.id,
        quantity=10,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    return equip, inventory


@pytest.fixture
async def donor_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a donor partner for testing."""
    tp = ThirdParty(name="Donor Org", type="partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        name="Donor Org",
        partner_type="donor",
        organization_type="NGO",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def referral_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a referral-only partner for testing."""
    tp = ThirdParty(name="Referral Only", type="partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        name="Referral Only",
        partner_type="referral",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def doctor(db_session: AsyncSession, admin_user: User) -> Doctor:
    """Create a doctor for testing."""
    tp = ThirdParty(name="Dr. Test", type="doctor", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    doctor = Doctor(
        third_party_id=tp.id,
        name="Dr. Test",
        specialization="General",
        type="internal",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def purchase_transaction(
    db_session: AsyncSession, admin_user: User, medicine_with_inventory: tuple,
) -> InventoryTransaction:
    """Create a purchase transaction with an item."""
    medicine, inventory = medicine_with_inventory
    transaction = InventoryTransaction(
        transaction_type="purchase",
        third_party_id=admin_user.third_party_id,
        transaction_date=date(2026, 3, 1),
        notes="Test purchase",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(transaction)
    await db_session.flush()
    await db_session.refresh(transaction)

    item = InventoryTransactionItem(
        transaction_id=transaction.id,
        item_type="medicine",
        item_id=medicine.id,
        quantity=50,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(item)

    # Update inventory quantity
    inventory.quantity += 50
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


class TestGetTransactions:
    """Tests for GET /api/v1/inventory-transactions"""

    @pytest.mark.asyncio
    async def test_get_transactions_authenticated(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test getting transactions list."""
        response = await client.get("/api/v1/inventory-transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_transactions_unauthenticated(self, client: AsyncClient):
        """Test getting transactions without authentication."""
        response = await client.get("/api/v1/inventory-transactions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_transactions_filter_by_type(
        self, client: AsyncClient, admin_headers: dict, purchase_transaction: InventoryTransaction,
    ):
        """Test filtering transactions by type."""
        response = await client.get(
            "/api/v1/inventory-transactions",
            params={"transaction_type": "purchase"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["transaction_type"] == "purchase"

    @pytest.mark.asyncio
    async def test_get_transactions_pagination(
        self, client: AsyncClient, admin_headers: dict, purchase_transaction: InventoryTransaction,
    ):
        """Test pagination works."""
        response = await client.get(
            "/api/v1/inventory-transactions",
            params={"page": 1, "size": 1},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1

    @pytest.mark.asyncio
    async def test_get_transactions_includes_third_party_name(
        self, client: AsyncClient, admin_headers: dict, purchase_transaction: InventoryTransaction,
    ):
        """Test that list response includes third_party_name."""
        response = await client.get("/api/v1/inventory-transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        item = data["items"][0]
        assert "third_party_name" in item


class TestGetTransaction:
    """Tests for GET /api/v1/inventory-transactions/{id}"""

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(
        self, client: AsyncClient, admin_headers: dict, purchase_transaction: InventoryTransaction,
    ):
        """Test getting transaction by ID includes items."""
        response = await client.get(
            f"/api/v1/inventory-transactions/{purchase_transaction.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "purchase"
        assert data["notes"] == "Test purchase"
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "third_party_name" in data

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent transaction."""
        response = await client.get("/api/v1/inventory-transactions/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateTransaction:
    """Tests for POST /api/v1/inventory-transactions"""

    @pytest.mark.asyncio
    async def test_create_purchase_transaction(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory: tuple, db_session: AsyncSession,
    ):
        """Test creating a purchase transaction (auto-sets third_party_id to user)."""
        medicine, inventory = medicine_with_inventory
        medicine_id = medicine.id
        original_qty = inventory.quantity

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "transaction_date": "2026-03-15",
                "notes": "Monthly purchase",
                "items": [
                    {"item_type": "medicine", "item_id": medicine_id, "quantity": 25},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "purchase"
        assert data["notes"] == "Monthly purchase"
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 25

        # Verify inventory was updated
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == original_qty + 25

    @pytest.mark.asyncio
    async def test_create_donation_transaction(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory: tuple, donor_partner: Partner, db_session: AsyncSession,
    ):
        """Test creating a donation transaction."""
        medicine, inventory = medicine_with_inventory
        medicine_id = medicine.id
        original_qty = inventory.quantity
        donor_tp_id = donor_partner.third_party_id

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "donation",
                "third_party_id": donor_tp_id,
                "transaction_date": "2026-03-15",
                "notes": "Donation from NGO",
                "items": [
                    {"item_type": "medicine", "item_id": medicine_id, "quantity": 30},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "donation"
        assert data["third_party_id"] == donor_tp_id

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == original_qty + 30

    @pytest.mark.asyncio
    async def test_create_prescription_transaction(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory: tuple, doctor: Doctor, db_session: AsyncSession,
    ):
        """Test creating a prescription transaction (decreases inventory)."""
        medicine, inventory = medicine_with_inventory
        medicine_id = medicine.id
        original_qty = inventory.quantity
        doctor_tp_id = doctor.third_party_id

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "prescription",
                "third_party_id": doctor_tp_id,
                "transaction_date": "2026-03-15",
                "notes": "Prescription for patient",
                "items": [
                    {"item_type": "medicine", "item_id": medicine_id, "quantity": 10},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "prescription"

        # Verify inventory decreased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == original_qty - 10

    @pytest.mark.asyncio
    async def test_create_loss_transaction(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory: tuple, db_session: AsyncSession,
    ):
        """Test creating a loss transaction (auto third_party, decreases inventory)."""
        medicine, inventory = medicine_with_inventory
        medicine_id = medicine.id
        original_qty = inventory.quantity

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "loss",
                "transaction_date": "2026-03-15",
                "notes": "Lost items",
                "items": [
                    {"item_type": "medicine", "item_id": medicine_id, "quantity": 5},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "loss"

        # Verify inventory decreased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == original_qty - 5

    @pytest.mark.asyncio
    async def test_create_transaction_without_items(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating a transaction without items."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "transaction_date": "2026-03-15",
                "notes": "Empty purchase",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["items"] == [] or data["items"] is None or len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_create_donation_without_third_party_fails(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test that donation without third_party_id fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "donation",
                "transaction_date": "2026-03-15",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "third_party_id" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_donation_with_referral_partner_fails(
        self, client: AsyncClient, admin_headers: dict, referral_partner: Partner,
    ):
        """Test that donation with referral-only partner fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "donation",
                "third_party_id": referral_partner.third_party_id,
                "transaction_date": "2026-03-15",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "donor" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_prescription_without_third_party_fails(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test that prescription without third_party_id fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "prescription",
                "transaction_date": "2026-03-15",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "third_party_id" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_prescription_with_non_doctor_fails(
        self, client: AsyncClient, admin_headers: dict, donor_partner: Partner,
    ):
        """Test that prescription with non-doctor third_party fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "prescription",
                "third_party_id": donor_partner.third_party_id,
                "transaction_date": "2026-03-15",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "doctor" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_transaction_insufficient_inventory_fails(
        self, client: AsyncClient, admin_headers: dict, medicine_with_inventory: tuple,
    ):
        """Test that prescribing more than available fails."""
        medicine, inventory = medicine_with_inventory
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "loss",
                "transaction_date": "2026-03-15",
                "items": [
                    {"item_type": "medicine", "item_id": medicine.id, "quantity": 99999},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_inventory_item_fails(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test that referencing non-existent inventory item fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "transaction_date": "2026-03-15",
                "items": [
                    {"item_type": "medicine", "item_id": 99999, "quantity": 10},
                ],
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "inventory record not found" in response.json()["detail"].lower()


class TestUpdateTransaction:
    """Tests for PUT /api/v1/inventory-transactions/{id}"""

    @pytest.mark.asyncio
    async def test_update_transaction_success(
        self, client: AsyncClient, admin_headers: dict,
        purchase_transaction: InventoryTransaction,
    ):
        """Test updating transaction notes and date."""
        response = await client.put(
            f"/api/v1/inventory-transactions/{purchase_transaction.id}",
            json={"notes": "Updated notes", "transaction_date": "2026-04-01"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["transaction_date"] == "2026-04-01"

    @pytest.mark.asyncio
    async def test_update_transaction_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent transaction."""
        response = await client.put(
            "/api/v1/inventory-transactions/99999",
            json={"notes": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteTransaction:
    """Tests for DELETE /api/v1/inventory-transactions/{id}"""

    @pytest.mark.asyncio
    async def test_delete_transaction_reverses_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, purchase_transaction: InventoryTransaction,
        medicine_with_inventory: tuple,
    ):
        """Test deleting transaction reverses inventory changes."""
        medicine, inventory = medicine_with_inventory
        medicine_id = medicine.id
        transaction_id = purchase_transaction.id
        # inventory was originally 100, purchase added 50 => 150
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        qty_before_delete = inv.quantity

        response = await client.delete(
            f"/api/v1/inventory-transactions/{transaction_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify inventory was reversed
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == qty_before_delete - 50

    @pytest.mark.asyncio
    async def test_delete_transaction_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent transaction."""
        response = await client.delete("/api/v1/inventory-transactions/99999", headers=admin_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_transaction_not_in_list(
        self, client: AsyncClient, admin_headers: dict,
        purchase_transaction: InventoryTransaction,
    ):
        """Test that deleted transaction is not returned in list."""
        await client.delete(
            f"/api/v1/inventory-transactions/{purchase_transaction.id}",
            headers=admin_headers,
        )
        response = await client.get("/api/v1/inventory-transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        ids = [t["id"] for t in data["items"]]
        assert purchase_transaction.id not in ids


class TestTransactionItems:
    """Tests for transaction item endpoints."""

    @pytest.mark.asyncio
    async def test_get_transaction_items(
        self, client: AsyncClient, admin_headers: dict,
        purchase_transaction: InventoryTransaction,
    ):
        """Test listing items for a transaction."""
        response = await client.get(
            f"/api/v1/inventory-transactions/{purchase_transaction.id}/items",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["item_type"] == "medicine"

    @pytest.mark.asyncio
    async def test_add_item_to_transaction(
        self, client: AsyncClient, admin_headers: dict,
        purchase_transaction: InventoryTransaction,
        equipment_with_inventory: tuple, db_session: AsyncSession,
    ):
        """Test adding an item to an existing transaction."""
        equip, inventory = equipment_with_inventory
        equip_id = equip.id
        original_qty = inventory.quantity
        transaction_id = purchase_transaction.id

        response = await client.post(
            f"/api/v1/inventory-transactions/{transaction_id}/items",
            json={"item_type": "equipment", "item_id": equip_id, "quantity": 5},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["item_type"] == "equipment"
        assert data["item_id"] == equip_id
        assert data["quantity"] == 5

        # Verify inventory was updated
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "equipment",
                Inventory.item_id == equip_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == original_qty + 5

    @pytest.mark.asyncio
    async def test_add_item_to_nonexistent_transaction(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory: tuple,
    ):
        """Test adding item to non-existent transaction."""
        medicine, _ = medicine_with_inventory
        response = await client.post(
            "/api/v1/inventory-transactions/99999/items",
            json={"item_type": "medicine", "item_id": medicine.id, "quantity": 5},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_transaction_item(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession,
        purchase_transaction: InventoryTransaction, medicine_with_inventory: tuple,
    ):
        """Test deleting a transaction item reverses inventory."""
        medicine, _ = medicine_with_inventory
        medicine_id = medicine.id
        transaction_id = purchase_transaction.id

        # Get the item id
        items_response = await client.get(
            f"/api/v1/inventory-transactions/{transaction_id}/items",
            headers=admin_headers,
        )
        items = items_response.json()
        item_id = items[0]["id"]

        # Get current inventory qty
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        qty_before = inv.quantity

        response = await client.delete(
            f"/api/v1/inventory-transaction-items/{item_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify inventory was reversed (purchase -> reversed = decrease by 50)
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == qty_before - 50

    @pytest.mark.asyncio
    async def test_delete_item_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent item."""
        response = await client.delete(
            "/api/v1/inventory-transaction-items/99999", headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_transaction_item(
        self, client: AsyncClient, admin_headers: dict,
        purchase_transaction: InventoryTransaction, medicine_with_inventory: tuple,
        db_session: AsyncSession,
    ):
        """Test updating a transaction item adjusts inventory."""
        medicine, _ = medicine_with_inventory
        medicine_id = medicine.id
        transaction_id = purchase_transaction.id

        # Get the item id
        items_response = await client.get(
            f"/api/v1/inventory-transactions/{transaction_id}/items",
            headers=admin_headers,
        )
        items = items_response.json()
        item_id = items[0]["id"]

        # Get current inventory qty (100 + 50 purchase = 150)
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        qty_before = inv.quantity

        # Update quantity from 50 to 30
        response = await client.put(
            f"/api/v1/inventory-transaction-items/{item_id}",
            json={"quantity": 30},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 30

        # Verify inventory: reverse old (150-50=100), apply new (100+30=130)
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == medicine_id,
            )
        )
        inv = result.scalar_one()
        assert inv.quantity == qty_before - 50 + 30
