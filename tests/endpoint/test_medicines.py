"""Tests for medicine endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medicine import Medicine
from app.model.medicine_category import MedicineCategory
from app.model.inventory import Inventory
from app.model.user import User


@pytest.fixture
async def medicine_category(db_session: AsyncSession, admin_user: User) -> MedicineCategory:
    """Create a medicine category for testing."""
    cat = MedicineCategory(
        name="Antibiotics",
        description="Anti-bacterial medicines",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


class TestGetMedicines:
    """Tests for GET /api/v1/medicines"""

    @pytest.mark.asyncio
    async def test_get_medicines_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting medicines list."""
        response = await client.get("/api/v1/medicines", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_medicines_unauthenticated(self, client: AsyncClient):
        """Test getting medicines without authentication."""
        response = await client.get("/api/v1/medicines")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_medicines_with_category_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, medicine_category: MedicineCategory
    ):
        """Test filtering medicines by category."""
        med = Medicine(
            name="Amoxicillin", category_id=medicine_category.id,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(med)
        await db_session.commit()

        response = await client.get(
            "/api/v1/medicines",
            params={"category_id": medicine_category.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["category_id"] == medicine_category.id

    @pytest.mark.asyncio
    async def test_get_medicines_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching medicines."""
        med1 = Medicine(name="Amoxicillin", description="Antibiotic", created_by=admin_user.username, updated_by=admin_user.username)
        med2 = Medicine(name="Ibuprofen", description="Painkiller", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([med1, med2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/medicines",
            params={"search": "Amox"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Amoxicillin"

    @pytest.mark.asyncio
    async def test_get_medicines_with_is_active_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test filtering by active status."""
        med1 = Medicine(name="Active Med", is_active=True, created_by=admin_user.username, updated_by=admin_user.username)
        med2 = Medicine(name="Inactive Med", is_active=False, created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([med1, med2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/medicines",
            params={"is_active": True},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_active"] is True


class TestGetMedicine:
    """Tests for GET /api/v1/medicines/{id}"""

    @pytest.mark.asyncio
    async def test_get_medicine_with_details(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, medicine_category: MedicineCategory
    ):
        """Test getting medicine by ID includes inventory and category info."""
        # Create medicine via API (auto-creates inventory)
        response = await client.post(
            "/api/v1/medicines",
            json={
                "name": "Amoxicillin",
                "category_id": medicine_category.id,
                "description": "Antibiotic",
                "unit": "tablets",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        medicine_id = response.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/medicines/{medicine_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Amoxicillin"
        assert data["category"]["name"] == "Antibiotics"
        assert data["inventory_quantity"] == 0

    @pytest.mark.asyncio
    async def test_get_medicine_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent medicine."""
        response = await client.get(
            "/api/v1/medicines/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateMedicine:
    """Tests for POST /api/v1/medicines"""

    @pytest.mark.asyncio
    async def test_create_medicine_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, medicine_category: MedicineCategory
    ):
        """Test creating a medicine and verify database state (including inventory)."""
        medicine_data = {
            "name": "Amoxicillin",
            "category_id": medicine_category.id,
            "description": "Broad-spectrum antibiotic",
            "unit": "tablets",
            "is_active": True,
        }

        response = await client.post(
            "/api/v1/medicines",
            json=medicine_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Amoxicillin"
        assert data["category_id"] == medicine_category.id
        assert data["unit"] == "tablets"

        # Verify medicine in database
        result = await db_session.execute(
            select(Medicine).where(Medicine.id == data["id"])
        )
        db_med = result.scalar_one_or_none()
        assert db_med is not None
        assert db_med.name == "Amoxicillin"
        assert db_med.created_by == admin_user.username

        # Verify inventory record was auto-created
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == data["id"],
            )
        )
        inventory = result.scalar_one_or_none()
        assert inventory is not None
        assert inventory.quantity == 0

    @pytest.mark.asyncio
    async def test_create_medicine_without_category(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating medicine without a category."""
        response = await client.post(
            "/api/v1/medicines",
            json={"name": "Generic Med", "unit": "ml"},
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] is None

    @pytest.mark.asyncio
    async def test_create_medicine_invalid_category(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating medicine with non-existent category."""
        response = await client.post(
            "/api/v1/medicines",
            json={"name": "Test Med", "category_id": 99999},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "category not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_medicine_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating medicine with duplicate name fails."""
        med = Medicine(name="Duplicate Med", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(med)
        await db_session.commit()

        response = await client.post(
            "/api/v1/medicines",
            json={"name": "Duplicate Med"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_medicine_empty_name(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating medicine with empty name fails."""
        response = await client.post(
            "/api/v1/medicines",
            json={"name": ""},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateMedicine:
    """Tests for PUT /api/v1/medicines/{id}"""

    @pytest.mark.asyncio
    async def test_update_medicine_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating a medicine and verify in database."""
        admin_username = admin_user.username

        med = Medicine(name="Old Name", unit="tablets", created_by=admin_username, updated_by=admin_username)
        db_session.add(med)
        await db_session.commit()
        await db_session.refresh(med)
        med_id = med.id

        response = await client.put(
            f"/api/v1/medicines/{med_id}",
            json={"name": "New Name", "unit": "ml"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["unit"] == "ml"

        # Verify database
        db_session.expire_all()
        result = await db_session.execute(
            select(Medicine).where(Medicine.id == med_id)
        )
        db_med = result.scalar_one_or_none()
        assert db_med.name == "New Name"
        assert db_med.updated_by == admin_username

    @pytest.mark.asyncio
    async def test_update_medicine_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent medicine."""
        response = await client.put(
            "/api/v1/medicines/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_medicine_invalid_category(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating medicine with non-existent category."""
        med = Medicine(name="Test Med", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(med)
        await db_session.commit()
        await db_session.refresh(med)

        response = await client.put(
            f"/api/v1/medicines/{med.id}",
            json={"category_id": 99999},
            headers=admin_headers,
        )
        assert response.status_code == 400


class TestDeleteMedicine:
    """Tests for DELETE /api/v1/medicines/{id}"""

    @pytest.mark.asyncio
    async def test_delete_medicine_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting medicine (soft delete) when inventory is 0."""
        # Create via API to auto-create inventory
        response = await client.post(
            "/api/v1/medicines",
            json={"name": "To Delete"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        med_id = response.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/medicines/{med_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(Medicine).where(Medicine.id == med_id)
        )
        db_med = result.scalar_one_or_none()
        assert db_med is not None
        assert db_med.is_deleted is True

        # Verify inventory also soft deleted
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medicine",
                Inventory.item_id == med_id,
            )
        )
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_medicine_with_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete medicine when inventory quantity > 0."""
        # Create medicine with inventory > 0
        med = Medicine(name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(med)
        await db_session.flush()
        await db_session.refresh(med)

        inv = Inventory(
            item_type="medicine", item_id=med.id, quantity=10,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/medicines/{med.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "inventory quantity" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_medicine_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent medicine."""
        response = await client.delete(
            "/api/v1/medicines/99999", headers=admin_headers
        )
        assert response.status_code == 404
