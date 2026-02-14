"""Tests for equipment category endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.equipment_category import EquipmentCategory
from app.model.equipment import Equipment
from app.model.user import User


class TestGetEquipmentCategories:
    """Tests for GET /api/v1/equipment-categories"""

    @pytest.mark.asyncio
    async def test_get_categories_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting categories list as authenticated user."""
        response = await client.get(
            "/api/v1/equipment-categories", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_categories_unauthenticated(self, client: AsyncClient):
        """Test getting categories without authentication."""
        response = await client.get("/api/v1/equipment-categories")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_categories_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching equipment categories."""
        cat1 = EquipmentCategory(name="Surgical", description="Surgical equipment", created_by=admin_user.id, updated_by=admin_user.id)
        cat2 = EquipmentCategory(name="Diagnostic", description="Diagnostic tools", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add_all([cat1, cat2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/equipment-categories",
            params={"search": "Surgical"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Surgical"


class TestGetEquipmentCategory:
    """Tests for GET /api/v1/equipment-categories/{id}"""

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting category by ID."""
        cat = EquipmentCategory(name="Lab Equipment", description="Laboratory tools", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        response = await client.get(
            f"/api/v1/equipment-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Lab Equipment"

    @pytest.mark.asyncio
    async def test_get_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent category."""
        response = await client.get(
            "/api/v1/equipment-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateEquipmentCategory:
    """Tests for POST /api/v1/equipment-categories"""

    @pytest.mark.asyncio
    async def test_create_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a new equipment category and verify in database."""
        response = await client.post(
            "/api/v1/equipment-categories",
            json={"name": "Surgical Tools", "description": "Tools for surgery"},
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Surgical Tools"

        # Verify in database
        result = await db_session.execute(
            select(EquipmentCategory).where(EquipmentCategory.id == data["id"])
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat is not None
        assert db_cat.name == "Surgical Tools"
        assert db_cat.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a category with duplicate name fails."""
        cat = EquipmentCategory(name="Duplicate", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()

        response = await client.post(
            "/api/v1/equipment-categories",
            json={"name": "Duplicate"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateEquipmentCategory:
    """Tests for PUT /api/v1/equipment-categories/{id}"""

    @pytest.mark.asyncio
    async def test_update_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating an equipment category."""
        cat = EquipmentCategory(name="Old Name", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        response = await client.put(
            f"/api/v1/equipment-categories/{cat.id}",
            json={"name": "Updated Name"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent category."""
        response = await client.put(
            "/api/v1/equipment-categories/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteEquipmentCategory:
    """Tests for DELETE /api/v1/equipment-categories/{id}"""

    @pytest.mark.asyncio
    async def test_delete_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting an equipment category (soft delete)."""
        cat = EquipmentCategory(name="To Delete", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)
        cat_id = cat.id

        response = await client.delete(
            f"/api/v1/equipment-categories/{cat_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(EquipmentCategory).where(EquipmentCategory.id == cat_id)
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_category_with_linked_equipment(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete category with linked equipment."""
        cat = EquipmentCategory(name="Has Equipment", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        equip = Equipment(name="Test Equip", category_id=cat.id, created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(equip)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/equipment-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "linked equipment" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent category."""
        response = await client.delete(
            "/api/v1/equipment-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404
