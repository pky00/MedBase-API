"""Tests for medicine category endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medicine_category import MedicineCategory
from app.model.medicine import Medicine
from app.model.user import User


class TestGetMedicineCategories:
    """Tests for GET /api/v1/medicine-categories"""

    @pytest.mark.asyncio
    async def test_get_categories_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting categories list as authenticated user."""
        response = await client.get(
            "/api/v1/medicine-categories", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    @pytest.mark.asyncio
    async def test_get_categories_unauthenticated(self, client: AsyncClient):
        """Test getting categories without authentication."""
        response = await client.get("/api/v1/medicine-categories")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_categories_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching medicine categories."""
        # Create categories
        cat1 = MedicineCategory(name="Antibiotics", description="Anti-bacterial medicines", created_by=admin_user.id, updated_by=admin_user.id)
        cat2 = MedicineCategory(name="Painkillers", description="Pain relief medicines", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add_all([cat1, cat2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/medicine-categories",
            params={"search": "Antibiotics"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Antibiotics"

    @pytest.mark.asyncio
    async def test_get_categories_pagination(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test pagination of medicine categories."""
        for i in range(5):
            cat = MedicineCategory(name=f"Category {i}", created_by=admin_user.id, updated_by=admin_user.id)
            db_session.add(cat)
        await db_session.commit()

        response = await client.get(
            "/api/v1/medicine-categories",
            params={"page": 1, "size": 2},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["pages"] == 3


class TestGetMedicineCategory:
    """Tests for GET /api/v1/medicine-categories/{id}"""

    @pytest.mark.asyncio
    async def test_get_category_by_id(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test getting category by ID."""
        cat = MedicineCategory(name="Vitamins", description="Vitamin supplements", created_by=admin_user.id, updated_by=admin_user.id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        response = await client.get(
            f"/api/v1/medicine-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cat.id
        assert data["name"] == "Vitamins"
        assert data["description"] == "Vitamin supplements"

    @pytest.mark.asyncio
    async def test_get_category_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting non-existent category."""
        response = await client.get(
            "/api/v1/medicine-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateMedicineCategory:
    """Tests for POST /api/v1/medicine-categories"""

    @pytest.mark.asyncio
    async def test_create_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a new medicine category and verify in database."""
        category_data = {
            "name": "Antibiotics",
            "description": "Anti-bacterial medicines",
        }

        response = await client.post(
            "/api/v1/medicine-categories",
            json=category_data,
            headers=admin_headers,
        )

        # Verify API response
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Antibiotics"
        assert data["description"] == "Anti-bacterial medicines"
        assert data["is_deleted"] is False

        # Verify database state
        result = await db_session.execute(
            select(MedicineCategory).where(MedicineCategory.id == data["id"])
        )
        db_cat = result.scalar_one_or_none()

        assert db_cat is not None
        assert db_cat.name == "Antibiotics"
        assert db_cat.description == "Anti-bacterial medicines"
        assert db_cat.created_by == admin_user.id
        assert db_cat.updated_by == admin_user.id
        assert db_cat.is_deleted is False

    @pytest.mark.asyncio
    async def test_create_category_name_only(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating a category with name only (description optional)."""
        response = await client.post(
            "/api/v1/medicine-categories",
            json={"name": "Supplements"},
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Supplements"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_category_empty_name(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating a category with empty name fails."""
        response = await client.post(
            "/api/v1/medicine-categories",
            json={"name": ""},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateMedicineCategory:
    """Tests for PUT /api/v1/medicine-categories/{id}"""

    @pytest.mark.asyncio
    async def test_update_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating a category and verify in database."""
        admin_id = admin_user.id

        cat = MedicineCategory(name="Old Name", description="Old Desc", created_by=admin_id, updated_by=admin_id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)
        cat_id = cat.id

        response = await client.put(
            f"/api/v1/medicine-categories/{cat_id}",
            json={"name": "New Name", "description": "New Desc"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New Desc"

        # Verify database
        db_session.expire_all()
        result = await db_session.execute(
            select(MedicineCategory).where(MedicineCategory.id == cat_id)
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat.name == "New Name"
        assert db_cat.updated_by == admin_id

    @pytest.mark.asyncio
    async def test_update_category_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test updating non-existent category."""
        response = await client.put(
            "/api/v1/medicine-categories/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteMedicineCategory:
    """Tests for DELETE /api/v1/medicine-categories/{id}"""

    @pytest.mark.asyncio
    async def test_delete_category_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting a category (soft delete) and verify in database."""
        admin_id = admin_user.id

        cat = MedicineCategory(name="To Delete", created_by=admin_id, updated_by=admin_id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)
        cat_id = cat.id

        response = await client.delete(
            f"/api/v1/medicine-categories/{cat_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted in database
        db_session.expire_all()
        result = await db_session.execute(
            select(MedicineCategory).where(MedicineCategory.id == cat_id)
        )
        db_cat = result.scalar_one_or_none()
        assert db_cat is not None
        assert db_cat.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_category_with_linked_medicines(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete category with linked medicines."""
        admin_id = admin_user.id

        cat = MedicineCategory(name="Has Medicines", created_by=admin_id, updated_by=admin_id)
        db_session.add(cat)
        await db_session.commit()
        await db_session.refresh(cat)

        med = Medicine(name="Test Med", category_id=cat.id, created_by=admin_id, updated_by=admin_id)
        db_session.add(med)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/medicine-categories/{cat.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "linked medicines" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_category_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test deleting non-existent category."""
        response = await client.delete(
            "/api/v1/medicine-categories/99999", headers=admin_headers
        )
        assert response.status_code == 404
