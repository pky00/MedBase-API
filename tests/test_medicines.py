import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.medicine import Medicine


class TestMedicineEndpoints:
    """Test cases for medicine endpoints."""

    @pytest.mark.asyncio
    async def test_create_medicine(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new medicine."""
        medicine_data = {
            "name": "Paracetamol 500mg",
            "generic_name": "Paracetamol",
            "brand_name": "Tylenol",
            "dosage_form": "tablet",
            "strength": "500mg",
            "unit": "mg",
            "code": "MED001",
            "requires_prescription": False,
        }
        response = await client.post(
            "/api/v1/medicines/",
            json=medicine_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == medicine_data["name"]
        assert data["dosage_form"] == medicine_data["dosage_form"]

        # Verify in database
        result = await db_session.execute(select(Medicine).where(Medicine.id == data["id"]))
        medicine = result.scalar_one_or_none()
        assert medicine is not None
        assert medicine.name == medicine_data["name"]

    @pytest.mark.asyncio
    async def test_create_medicine_duplicate_code(self, client: AsyncClient, admin_headers: dict):
        """Test creating medicine with duplicate code fails."""
        medicine_data = {
            "name": "Medicine 1",
            "dosage_form": "tablet",
            "unit": "mg",
            "code": "DUPMED001",
        }
        await client.post("/api/v1/medicines/", json=medicine_data, headers=admin_headers)

        medicine_data["name"] = "Medicine 2"
        response = await client.post("/api/v1/medicines/", json=medicine_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Medicine code already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_medicines(self, client: AsyncClient, admin_headers: dict):
        """Test listing medicines."""
        await client.post(
            "/api/v1/medicines/",
            json={"name": "List Test Med", "dosage_form": "capsule", "unit": "mg"},
            headers=admin_headers,
        )

        response = await client.get("/api/v1/medicines/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_medicines_search(self, client: AsyncClient, admin_headers: dict):
        """Test searching medicines."""
        await client.post(
            "/api/v1/medicines/",
            json={"name": "Amoxicillin 250mg", "generic_name": "Amoxicillin", "dosage_form": "capsule", "unit": "mg"},
            headers=admin_headers,
        )

        response = await client.get("/api/v1/medicines/?search=Amoxicillin", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_medicine_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting a medicine by ID."""
        create_response = await client.post(
            "/api/v1/medicines/",
            json={"name": "Get Test Med", "dosage_form": "syrup", "unit": "ml"},
            headers=admin_headers,
        )
        medicine_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/medicines/{medicine_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == medicine_id

    @pytest.mark.asyncio
    async def test_update_medicine(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a medicine."""
        create_response = await client.post(
            "/api/v1/medicines/",
            json={"name": "Update Test Med", "dosage_form": "tablet", "unit": "mg"},
            headers=admin_headers,
        )
        medicine_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/medicines/{medicine_id}",
            json={"name": "Updated Medicine Name", "is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Medicine Name"
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_medicine(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a medicine."""
        create_response = await client.post(
            "/api/v1/medicines/",
            json={"name": "Delete Test Med", "dosage_form": "injection", "unit": "ml"},
            headers=admin_headers,
        )
        medicine_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/medicines/{medicine_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(Medicine).where(Medicine.id == medicine_id))
        assert result.scalar_one_or_none() is None

