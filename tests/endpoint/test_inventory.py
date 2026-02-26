"""Tests for inventory endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.inventory import Inventory
from app.model.user import User


class TestGetInventory:
    """Tests for GET /api/v1/inventory"""

    @pytest.mark.asyncio
    async def test_get_inventory_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting inventory list."""
        response = await client.get("/api/v1/inventory", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_inventory_unauthenticated(self, client: AsyncClient):
        """Test getting inventory without authentication."""
        response = await client.get("/api/v1/inventory")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_inventory_with_item_type_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test filtering inventory by item type."""
        inv1 = Inventory(
            item_type="medicine", item_id=1, quantity=10,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        inv2 = Inventory(
            item_type="equipment", item_id=1, quantity=5,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add_all([inv1, inv2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/inventory",
            params={"item_type": "medicine"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["item_type"] == "medicine"

    @pytest.mark.asyncio
    async def test_get_inventory_pagination(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test inventory pagination."""
        for i in range(5):
            inv = Inventory(
                item_type="medicine", item_id=i + 1, quantity=i,
                created_by=admin_user.username, updated_by=admin_user.username,
            )
            db_session.add(inv)
        await db_session.commit()

        response = await client.get(
            "/api/v1/inventory",
            params={"page": 1, "size": 2},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


class TestGetInventoryById:
    """Tests for GET /api/v1/inventory/{id}"""

    @pytest.mark.asyncio
    async def test_get_inventory_by_id(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting inventory by ID."""
        inv = Inventory(
            item_type="medicine", item_id=1, quantity=10,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()
        await db_session.refresh(inv)

        response = await client.get(
            f"/api/v1/inventory/{inv.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_type"] == "medicine"
        assert data["quantity"] == 10

    @pytest.mark.asyncio
    async def test_get_inventory_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent inventory record."""
        response = await client.get(
            "/api/v1/inventory/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestGetInventoryByItem:
    """Tests for GET /api/v1/inventory/item/{item_type}/{item_id}"""

    @pytest.mark.asyncio
    async def test_get_inventory_by_item(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting inventory by item type and ID."""
        inv = Inventory(
            item_type="equipment", item_id=42, quantity=7,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.get(
            "/api/v1/inventory/item/equipment/42", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_type"] == "equipment"
        assert data["item_id"] == 42
        assert data["quantity"] == 7

    @pytest.mark.asyncio
    async def test_get_inventory_by_item_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting inventory for non-existent item."""
        response = await client.get(
            "/api/v1/inventory/item/medicine/99999", headers=admin_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_inventory_by_item_invalid_type(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting inventory with invalid item type."""
        response = await client.get(
            "/api/v1/inventory/item/invalid_type/1", headers=admin_headers
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_inventory_auto_created_with_medicine(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test that creating a medicine auto-creates an inventory record."""
        # Create a medicine via the API
        response = await client.post(
            "/api/v1/medicines",
            json={"name": "Auto Inventory Med"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        medicine_id = response.json()["id"]

        # Verify inventory was created
        response = await client.get(
            f"/api/v1/inventory/item/medicine/{medicine_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["item_type"] == "medicine"
        assert data["item_id"] == medicine_id
        assert data["quantity"] == 0
