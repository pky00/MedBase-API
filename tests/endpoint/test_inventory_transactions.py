"""Tests for inventory transaction endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medicine import Medicine
from app.model.equipment import Equipment
from app.model.inventory import Inventory
from app.model.inventory_transaction import InventoryTransaction
from app.model.user import User


@pytest.fixture
async def medicine_with_inventory(db_session: AsyncSession, admin_user: User):
    """Create a medicine with an inventory record."""
    med = Medicine(
        name="TX Test Medicine",
        description="For transaction tests",
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(med)
    await db_session.flush()
    await db_session.refresh(med)

    inv = Inventory(
        item_type="medicine",
        item_id=med.id,
        quantity=100,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(med)
    await db_session.refresh(inv)
    return med, inv


@pytest.fixture
async def equipment_with_inventory(db_session: AsyncSession, admin_user: User):
    """Create equipment with an inventory record."""
    eq = Equipment(
        name="TX Test Equipment",
        condition="new",
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(eq)
    await db_session.flush()
    await db_session.refresh(eq)

    inv = Inventory(
        item_type="equipment",
        item_id=eq.id,
        quantity=20,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(inv)
    await db_session.commit()
    await db_session.refresh(eq)
    await db_session.refresh(inv)
    return eq, inv


class TestGetInventoryTransactions:
    """Tests for GET /api/v1/inventory-transactions"""

    @pytest.mark.asyncio
    async def test_get_transactions_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
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
    async def test_get_transactions_filter_by_transaction_type(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test filtering transactions by transaction_type."""
        med, _ = medicine_with_inventory

        # Create a purchase transaction
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 10,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201

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
    async def test_get_transactions_filter_by_item_type(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test filtering transactions by item_type."""
        med, _ = medicine_with_inventory

        await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 5,
            },
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/inventory-transactions",
            params={"item_type": "medicine"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["item_type"] == "medicine"

    @pytest.mark.asyncio
    async def test_get_transactions_filter_by_item_id(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test filtering transactions by item_id."""
        med, _ = medicine_with_inventory

        await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 5,
            },
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/inventory-transactions",
            params={"item_id": med.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["item_id"] == med.id


class TestGetInventoryTransaction:
    """Tests for GET /api/v1/inventory-transactions/{id}"""

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory,
    ):
        """Test getting transaction by ID."""
        med, _ = medicine_with_inventory

        # Create transaction
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 10,
                "notes": "Test purchase",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        tx_id = response.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/inventory-transactions/{tx_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "purchase"
        assert data["item_type"] == "medicine"
        assert data["quantity"] == 10
        assert data["notes"] == "Test purchase"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent transaction."""
        response = await client.get(
            "/api/v1/inventory-transactions/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateInventoryTransaction:
    """Tests for POST /api/v1/inventory-transactions"""

    @pytest.mark.asyncio
    async def test_create_purchase_increases_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test creating a purchase transaction increases inventory."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 50,
                "notes": "Bulk purchase",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "purchase"
        assert data["quantity"] == 50

        # Verify transaction in database
        result = await db_session.execute(
            select(InventoryTransaction).where(InventoryTransaction.id == data["id"])
        )
        db_tx = result.scalar_one_or_none()
        assert db_tx is not None
        assert db_tx.created_by == admin_user.id

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty + 50

    @pytest.mark.asyncio
    async def test_create_donation_increases_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test creating a donation transaction increases inventory."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "donation",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 30,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty + 30

    @pytest.mark.asyncio
    async def test_create_loss_decreases_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test creating a loss transaction decreases inventory."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity  # 100

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "loss",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 10,
                "notes": "Damaged in storage",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201

        # Verify inventory decreased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty - 10

    @pytest.mark.asyncio
    async def test_create_breakage_decreases_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, equipment_with_inventory,
    ):
        """Test creating a breakage transaction decreases inventory."""
        eq, inv = equipment_with_inventory
        initial_qty = inv.quantity

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "breakage",
                "item_type": "equipment",
                "item_id": eq.id,
                "quantity": 2,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201

        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "equipment",
                Inventory.item_id == eq.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == initial_qty - 2

    @pytest.mark.asyncio
    async def test_create_transaction_inventory_floor_zero(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, admin_user: User,
    ):
        """Test that inventory cannot go below 0."""
        med = Medicine(
            name="Floor Test Medicine",
            created_by=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(med)
        await db_session.flush()

        inv = Inventory(
            item_type="medicine",
            item_id=med.id,
            quantity=5,
            created_by=admin_user.id,
            updated_by=admin_user.id,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "loss",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 100,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201

        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        updated_inv = result.scalar_one_or_none()
        assert updated_inv.quantity == 0

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_item(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating transaction with non-existent item fails."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": 99999,
                "quantity": 10,
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Item not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_type(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating transaction with invalid transaction_type."""
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "invalid_type",
                "item_type": "medicine",
                "item_id": 1,
                "quantity": 10,
            },
            headers=admin_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_transaction_zero_quantity(
        self, client: AsyncClient, admin_headers: dict,
        medicine_with_inventory,
    ):
        """Test creating transaction with zero quantity fails."""
        med, _ = medicine_with_inventory

        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 0,
            },
            headers=admin_headers,
        )

        assert response.status_code == 422


class TestDeleteInventoryTransaction:
    """Tests for DELETE /api/v1/inventory-transactions/{id}"""

    @pytest.mark.asyncio
    async def test_delete_purchase_reverses_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test deleting a purchase transaction reverses the inventory increase."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity

        # Create purchase transaction
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "purchase",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 25,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        tx_id = response.json()["id"]

        # Verify inventory increased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == initial_qty + 25

        # Delete transaction
        response = await client.delete(
            f"/api/v1/inventory-transactions/{tx_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify inventory reversed
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == initial_qty

        # Verify transaction soft deleted
        result = await db_session.execute(
            select(InventoryTransaction).where(InventoryTransaction.id == tx_id)
        )
        db_tx = result.scalar_one_or_none()
        assert db_tx.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_loss_reverses_inventory(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medicine_with_inventory,
    ):
        """Test deleting a loss transaction reverses the inventory decrease (re-adds stock)."""
        med, inv = medicine_with_inventory
        initial_qty = inv.quantity  # 100

        # Create loss transaction
        response = await client.post(
            "/api/v1/inventory-transactions",
            json={
                "transaction_type": "loss",
                "item_type": "medicine",
                "item_id": med.id,
                "quantity": 15,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        tx_id = response.json()["id"]

        # Verify inventory decreased
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == initial_qty - 15

        # Delete transaction
        response = await client.delete(
            f"/api/v1/inventory-transactions/{tx_id}", headers=admin_headers
        )
        assert response.status_code == 200

        # Verify inventory restored
        db_session.expire_all()
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med.id,
            )
        )
        assert result.scalar_one_or_none().quantity == initial_qty

    @pytest.mark.asyncio
    async def test_delete_transaction_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent transaction."""
        response = await client.delete(
            "/api/v1/inventory-transactions/99999", headers=admin_headers
        )
        assert response.status_code == 404
