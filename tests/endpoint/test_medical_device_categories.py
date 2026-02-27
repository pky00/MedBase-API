"""Tests for medical device category endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medical_device_category import MedicalDeviceCategory
from app.model.medical_device import MedicalDevice
from app.model.user import User


class TestGetMedicalDeviceCategories:
    """Tests for GET /api/v1/medical-device-categories"""

    @pytest.mark.asyncio
    async def test_get_categories_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting categories list as authenticated user."""
        response = await client.get(
            "/api/v1/medical-device-categories", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_categories_unauthenticated(self, client: AsyncClient):
        """Test getting categories without authentication."""
        response = await client.get("/api/v1/medical-device-categories")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_categories_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching medical device categories."""
        cat1 = MedicalDeviceCategory(name="Monitors", description="Patient monitors", created_by=admin_user.username, updated_by=admin_user.username)
        cat2 = MedicalDeviceCategory(name="Pumps", description="Infusion pumps", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([cat1, cat2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/medical-device-categories",
            params={"search": "Monitors"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Monitors"


class TestGetMedicalDeviceCategory:
    """Tests for GET /api/v1/medical-device-categories/{id}"""

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting category by ID."""
        cat = MedicalDeviceCategory(name="Imaging", description="Imaging devices", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        response = await client.get(
            f"/api/v1/medical-device-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Imaging"

    @pytest.mark.asyncio
    async def test_get_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent category."""
        response = await client.get(
            "/api/v1/medical-device-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateMedicalDeviceCategory:
    """Tests for POST /api/v1/medical-device-categories"""

    @pytest.mark.asyncio
    async def test_create_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a new medical device category and verify in database."""
        response = await client.post(
            "/api/v1/medical-device-categories",
            json={"name": "Respiratory", "description": "Respiratory devices"},
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Respiratory"

        # Verify in database
        result = await db_session.execute(
            select(MedicalDeviceCategory).where(MedicalDeviceCategory.id == data["id"])
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat is not None
        assert db_cat.name == "Respiratory"
        assert db_cat.created_by == admin_user.username

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a category with duplicate name fails."""
        cat = MedicalDeviceCategory(name="Duplicate", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(cat)
        await db_session.commit()

        response = await client.post(
            "/api/v1/medical-device-categories",
            json={"name": "Duplicate"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateMedicalDeviceCategory:
    """Tests for PUT /api/v1/medical-device-categories/{id}"""

    @pytest.mark.asyncio
    async def test_update_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating a medical device category."""
        cat = MedicalDeviceCategory(name="Old Name", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        response = await client.put(
            f"/api/v1/medical-device-categories/{cat.id}",
            json={"name": "Updated Name"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent category."""
        response = await client.put(
            "/api/v1/medical-device-categories/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteMedicalDeviceCategory:
    """Tests for DELETE /api/v1/medical-device-categories/{id}"""

    @pytest.mark.asyncio
    async def test_delete_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting a medical device category (soft delete)."""
        cat = MedicalDeviceCategory(name="To Delete", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)
        cat_id = cat.id

        response = await client.delete(
            f"/api/v1/medical-device-categories/{cat_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(MedicalDeviceCategory).where(MedicalDeviceCategory.id == cat_id)
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_category_with_linked_devices(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete category with linked medical devices."""
        cat = MedicalDeviceCategory(name="Has Devices", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        device = MedicalDevice(name="Test Device", category_id=cat.id, created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(device)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/medical-device-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "linked medical devices" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent category."""
        response = await client.delete(
            "/api/v1/medical-device-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404
