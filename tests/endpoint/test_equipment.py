"""Tests for equipment endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.equipment import Equipment
from app.model.equipment_category import EquipmentCategory
from app.model.inventory import Inventory
from app.model.item import Item
from app.model.user import User


@pytest.fixture
async def equipment_category(db_session: AsyncSession, admin_user: User) -> EquipmentCategory:
    """Create an equipment category for testing."""
    cat = EquipmentCategory(
        name="Surgical Tools",
        description="Tools used in surgery",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


class TestGetEquipment:
    """Tests for GET /api/v1/equipment"""

    @pytest.mark.asyncio
    async def test_get_equipment_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        response = await client.get("/api/v1/equipment", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_equipment_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/equipment")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_equipment_with_condition_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        item1 = Item(item_type="equipment", name="New Scalpel", created_by=admin_user.username, updated_by=admin_user.username)
        item2 = Item(item_type="equipment", name="Old Scalpel", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([item1, item2])
        await db_session.flush()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        e1 = Equipment(item_id=item1.id, code="EQ-NSC", name="New Scalpel", condition="new", created_by=admin_user.username, updated_by=admin_user.username)
        e2 = Equipment(item_id=item2.id, code="EQ-OSC", name="Old Scalpel", condition="poor", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([e1, e2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/equipment",
            params={"condition": "new"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item_resp in data["items"]:
            assert item_resp["condition"] == "new"

    @pytest.mark.asyncio
    async def test_get_equipment_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        item1 = Item(item_type="equipment", name="Scalpel", created_by=admin_user.username, updated_by=admin_user.username)
        item2 = Item(item_type="equipment", name="Stethoscope", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([item1, item2])
        await db_session.flush()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        e1 = Equipment(item_id=item1.id, code="EQ-SCA", name="Scalpel", created_by=admin_user.username, updated_by=admin_user.username)
        e2 = Equipment(item_id=item2.id, code="EQ-STH", name="Stethoscope", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([e1, e2])
        await db_session.commit()

        response = await client.get("/api/v1/equipment", params={"search": "Scalpel"}, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Scalpel"


class TestGetEquipmentById:
    """Tests for GET /api/v1/equipment/{id}"""

    @pytest.mark.asyncio
    async def test_get_equipment_with_details(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, equipment_category: EquipmentCategory
    ):
        response = await client.post(
            "/api/v1/equipment",
            json={"code": "EQ-SC1", "name": "Scalpel", "category_id": equipment_category.id, "condition": "new"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        equip_id = response.json()["id"]

        response = await client.get(f"/api/v1/equipment/{equip_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Scalpel"
        assert data["category"]["name"] == "Surgical Tools"
        assert data["inventory_quantity"] == 0
        assert "item_id" in data

    @pytest.mark.asyncio
    async def test_get_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/api/v1/equipment/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateEquipment:
    """Tests for POST /api/v1/equipment"""

    @pytest.mark.asyncio
    async def test_create_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, equipment_category: EquipmentCategory
    ):
        response = await client.post(
            "/api/v1/equipment",
            json={"code": "EQ-SSC", "name": "Surgical Scalpel", "category_id": equipment_category.id, "description": "Precision scalpel", "condition": "new", "is_active": True},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Surgical Scalpel"
        assert data["condition"] == "new"
        assert "item_id" in data

        # Verify in database
        result = await db_session.execute(select(Equipment).where(Equipment.id == data["id"]))
        db_equip = result.scalar_one_or_none()
        assert db_equip is not None
        assert db_equip.item_id is not None

        # Verify inventory auto-created
        result = await db_session.execute(select(Inventory).where(Inventory.item_id == db_equip.item_id))
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.quantity == 0

    @pytest.mark.asyncio
    async def test_create_equipment_invalid_condition(self, client: AsyncClient, admin_headers: dict):
        response = await client.post("/api/v1/equipment", json={"code": "EQ-INV", "name": "Test", "condition": "invalid"}, headers=admin_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_equipment_invalid_category(self, client: AsyncClient, admin_headers: dict):
        response = await client.post("/api/v1/equipment", json={"code": "EQ-IC1", "name": "Test", "category_id": 99999}, headers=admin_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_equipment_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        item = Item(item_type="equipment", name="Duplicate Equip", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        equip = Equipment(item_id=item.id, code="EQ-DUP", name="Duplicate Equip", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(equip)
        await db_session.commit()

        response = await client.post("/api/v1/equipment", json={"code": "EQ-DU2", "name": "Duplicate Equip"}, headers=admin_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateEquipment:
    """Tests for PUT /api/v1/equipment/{id}"""

    @pytest.mark.asyncio
    async def test_update_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        admin_username = admin_user.username
        item = Item(item_type="equipment", name="Old Name", created_by=admin_username, updated_by=admin_username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        equip = Equipment(item_id=item.id, code="EQ-OLD", name="Old Name", condition="good", created_by=admin_username, updated_by=admin_username)
        db_session.add(equip)
        await db_session.commit()
        await db_session.refresh(equip)
        equip_id = equip.id

        response = await client.put(f"/api/v1/equipment/{equip_id}", json={"name": "New Name", "condition": "fair"}, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["condition"] == "fair"

    @pytest.mark.asyncio
    async def test_update_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.put("/api/v1/equipment/99999", json={"name": "Test"}, headers=admin_headers)
        assert response.status_code == 404


class TestDeleteEquipment:
    """Tests for DELETE /api/v1/equipment/{id}"""

    @pytest.mark.asyncio
    async def test_delete_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        response = await client.post("/api/v1/equipment", json={"code": "EQ-DEL", "name": "To Delete", "condition": "new"}, headers=admin_headers)
        assert response.status_code == 201
        equip_id = response.json()["id"]
        item_id = response.json()["item_id"]

        response = await client.delete(f"/api/v1/equipment/{equip_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(select(Equipment).where(Equipment.id == equip_id))
        db_equip = result.scalar_one_or_none()
        assert db_equip.is_deleted is True

        result = await db_session.execute(select(Inventory).where(Inventory.item_id == item_id))
        inv = result.scalar_one_or_none()
        assert inv.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_equipment_with_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        item = Item(item_type="equipment", name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        equip = Equipment(item_id=item.id, code="EQ-STK", name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(equip)
        await db_session.flush()
        await db_session.refresh(equip)

        inv = Inventory(item_id=item.id, quantity=5, created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(inv)
        await db_session.commit()

        response = await client.delete(f"/api/v1/equipment/{equip.id}", headers=admin_headers)
        assert response.status_code == 400
        assert "inventory quantity" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.delete("/api/v1/equipment/99999", headers=admin_headers)
        assert response.status_code == 404
