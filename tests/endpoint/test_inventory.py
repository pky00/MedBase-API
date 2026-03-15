"""Tests for inventory endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.inventory import Inventory
from app.model.item import Item
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
        item1 = Item(item_type="medicine", name="Filter Med", created_by=admin_user.username, updated_by=admin_user.username)
        item2 = Item(item_type="equipment", name="Filter Equip", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([item1, item2])
        await db_session.flush()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        inv1 = Inventory(
            item_id=item1.id, quantity=10,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        inv2 = Inventory(
            item_id=item2.id, quantity=5,
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
            item = Item(item_type="medicine", name=f"Paginate Med {i}", created_by=admin_user.username, updated_by=admin_user.username)
            db_session.add(item)
            await db_session.flush()
            await db_session.refresh(item)

            inv = Inventory(
                item_id=item.id, quantity=i,
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
        item = Item(item_type="medicine", name="ById Med", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        inv = Inventory(
            item_id=item.id, quantity=10,
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
    """Tests for GET /api/v1/inventory/item/{item_id}"""

    @pytest.mark.asyncio
    async def test_get_inventory_by_item(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting inventory by item ID."""
        item = Item(item_type="equipment", name="ByItem Equip", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        inv = Inventory(
            item_id=item.id, quantity=7,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/inventory/item/{item.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_type"] == "equipment"
        assert data["item_id"] == item.id
        assert data["quantity"] == 7

    @pytest.mark.asyncio
    async def test_get_inventory_by_item_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting inventory for non-existent item."""
        response = await client.get(
            "/api/v1/inventory/item/99999", headers=admin_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_inventory_auto_created_with_medicine(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test that creating a medicine auto-creates an inventory record."""
        response = await client.post(
            "/api/v1/medicines",
            json={"code": "AINV01", "name": "Auto Inventory Med"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        item_id = response.json()["item_id"]

        response = await client.get(
            f"/api/v1/inventory/item/{item_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["item_type"] == "medicine"
        assert data["item_id"] == item_id
        assert data["quantity"] == 0
