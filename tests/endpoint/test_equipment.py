"""Tests for equipment endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.equipment import Equipment
from app.model.equipment_category import EquipmentCategory
from app.model.inventory import Inventory
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
        """Test getting equipment list."""
        response = await client.get("/api/v1/equipment", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_equipment_unauthenticated(self, client: AsyncClient):
        """Test getting equipment without authentication."""
        response = await client.get("/api/v1/equipment")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_equipment_with_condition_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test filtering equipment by condition."""
        e1 = Equipment(name="New Scalpel", condition="new", created_by=admin_user.username, updated_by=admin_user.username)
        e2 = Equipment(name="Old Scalpel", condition="poor", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([e1, e2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/equipment",
            params={"condition": "new"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["condition"] == "new"

    @pytest.mark.asyncio
    async def test_get_equipment_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching equipment."""
        e1 = Equipment(name="Scalpel", created_by=admin_user.username, updated_by=admin_user.username)
        e2 = Equipment(name="Stethoscope", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([e1, e2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/equipment",
            params={"search": "Scalpel"},
            headers=admin_headers,
        )

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
        """Test getting equipment by ID includes inventory and category."""
        response = await client.post(
            "/api/v1/equipment",
            json={
                "name": "Scalpel",
                "category_id": equipment_category.id,
                "condition": "new",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        equip_id = response.json()["id"]

        response = await client.get(
            f"/api/v1/equipment/{equip_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Scalpel"
        assert data["category"]["name"] == "Surgical Tools"
        assert data["inventory_quantity"] == 0

    @pytest.mark.asyncio
    async def test_get_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent equipment."""
        response = await client.get("/api/v1/equipment/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateEquipment:
    """Tests for POST /api/v1/equipment"""

    @pytest.mark.asyncio
    async def test_create_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, equipment_category: EquipmentCategory
    ):
        """Test creating equipment and verify database state."""
        equipment_data = {
            "name": "Surgical Scalpel",
            "category_id": equipment_category.id,
            "description": "Precision scalpel",
            "condition": "new",
            "is_active": True,
        }

        response = await client.post(
            "/api/v1/equipment",
            json=equipment_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Surgical Scalpel"
        assert data["condition"] == "new"

        # Verify in database
        result = await db_session.execute(
            select(Equipment).where(Equipment.id == data["id"])
        )
        db_equip = result.scalar_one_or_none()
        assert db_equip is not None
        assert db_equip.name == "Surgical Scalpel"
        assert db_equip.created_by == admin_user.username

        # Verify inventory auto-created
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "equipment",
                Inventory.item_id == data["id"],
            )
        )
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.quantity == 0

    @pytest.mark.asyncio
    async def test_create_equipment_invalid_condition(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating equipment with invalid condition."""
        response = await client.post(
            "/api/v1/equipment",
            json={"name": "Test", "condition": "invalid"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_equipment_invalid_category(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating equipment with non-existent category."""
        response = await client.post(
            "/api/v1/equipment",
            json={"name": "Test", "category_id": 99999},
            headers=admin_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_equipment_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating equipment with duplicate name fails."""
        equip = Equipment(name="Duplicate Equip", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(equip)
        await db_session.commit()

        response = await client.post(
            "/api/v1/equipment",
            json={"name": "Duplicate Equip"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateEquipment:
    """Tests for PUT /api/v1/equipment/{id}"""

    @pytest.mark.asyncio
    async def test_update_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating equipment and verify in database."""
        admin_username = admin_user.username
        equip = Equipment(name="Old Name", condition="good", created_by=admin_username, updated_by=admin_username)
        db_session.add(equip)
        await db_session.commit()
        await db_session.refresh(equip)
        equip_id = equip.id

        response = await client.put(
            f"/api/v1/equipment/{equip_id}",
            json={"name": "New Name", "condition": "fair"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["condition"] == "fair"

        # Verify database
        db_session.expire_all()
        result = await db_session.execute(
            select(Equipment).where(Equipment.id == equip_id)
        )
        db_equip = result.scalar_one_or_none()
        assert db_equip.name == "New Name"
        assert db_equip.updated_by == admin_username

    @pytest.mark.asyncio
    async def test_update_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent equipment."""
        response = await client.put(
            "/api/v1/equipment/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteEquipment:
    """Tests for DELETE /api/v1/equipment/{id}"""

    @pytest.mark.asyncio
    async def test_delete_equipment_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting equipment when inventory is 0."""
        response = await client.post(
            "/api/v1/equipment",
            json={"name": "To Delete", "condition": "new"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        equip_id = response.json()["id"]

        response = await client.delete(
            f"/api/v1/equipment/{equip_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(Equipment).where(Equipment.id == equip_id)
        )
        db_equip = result.scalar_one_or_none()
        assert db_equip.is_deleted is True

        # Verify inventory also soft deleted
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "equipment",
                Inventory.item_id == equip_id,
            )
        )
        inv = result.scalar_one_or_none()
        assert inv.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_equipment_with_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete equipment when inventory quantity > 0."""
        equip = Equipment(name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(equip)
        await db_session.flush()
        await db_session.refresh(equip)

        inv = Inventory(
            item_type="equipment", item_id=equip.id, quantity=5,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/equipment/{equip.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "inventory quantity" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_equipment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent equipment."""
        response = await client.delete(
            "/api/v1/equipment/99999", headers=admin_headers
        )
        assert response.status_code == 404
