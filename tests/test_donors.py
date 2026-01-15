import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.donor import Donor


class TestDonorEndpoints:
    """Test cases for donor endpoints."""

    @pytest.mark.asyncio
    async def test_create_donor(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new donor."""
        donor_data = {
            "name": "Test Foundation",
            "donor_type": "organization",
            "donor_code": "DON001",
            "contact_person": "John Doe",
            "phone": "1234567890",
            "email": "foundation@example.com",
            "city": "Test City",
            "country": "Test Country",
        }
        response = await client.post(
            "/api/v1/donors/",
            json=donor_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == donor_data["name"]
        assert data["donor_type"] == donor_data["donor_type"]
        assert data["donor_code"] == donor_data["donor_code"]

        # Verify in database
        result = await db_session.execute(select(Donor).where(Donor.id == data["id"]))
        donor = result.scalar_one_or_none()
        assert donor is not None
        assert donor.name == donor_data["name"]

    @pytest.mark.asyncio
    async def test_create_donor_duplicate_code(self, client: AsyncClient, admin_headers: dict):
        """Test creating donor with duplicate code fails."""
        donor_data = {
            "name": "First Foundation",
            "donor_type": "individual",
            "donor_code": "DUP001",
        }
        await client.post("/api/v1/donors/", json=donor_data, headers=admin_headers)

        donor_data["name"] = "Second Foundation"
        response = await client.post("/api/v1/donors/", json=donor_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Donor code already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_donors(self, client: AsyncClient, admin_headers: dict):
        """Test listing donors."""
        # Create a donor first
        await client.post(
            "/api/v1/donors/",
            json={"name": "List Test Donor", "donor_type": "individual"},
            headers=admin_headers,
        )

        response = await client.get("/api/v1/donors/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_donors_filter_by_type(self, client: AsyncClient, admin_headers: dict):
        """Test filtering donors by type."""
        await client.post(
            "/api/v1/donors/",
            json={"name": "NGO Donor", "donor_type": "ngo"},
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/donors/?donor_type=ngo",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for donor in data["data"]:
            assert donor["donor_type"] == "ngo"

    @pytest.mark.asyncio
    async def test_get_donor_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting a donor by ID."""
        create_response = await client.post(
            "/api/v1/donors/",
            json={"name": "Get Test Donor", "donor_type": "individual"},
            headers=admin_headers,
        )
        donor_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/donors/{donor_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == donor_id

    @pytest.mark.asyncio
    async def test_get_donor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent donor returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/donors/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_donor(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a donor."""
        create_response = await client.post(
            "/api/v1/donors/",
            json={"name": "Update Test Donor", "donor_type": "individual"},
            headers=admin_headers,
        )
        donor_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/donors/{donor_id}",
            json={"name": "Updated Donor Name", "city": "New City"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Donor Name"
        assert response.json()["city"] == "New City"

        # Verify in database
        result = await db_session.execute(select(Donor).where(Donor.id == donor_id))
        donor = result.scalar_one_or_none()
        assert donor.name == "Updated Donor Name"

    @pytest.mark.asyncio
    async def test_delete_donor(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a donor."""
        create_response = await client.post(
            "/api/v1/donors/",
            json={"name": "Delete Test Donor", "donor_type": "individual"},
            headers=admin_headers,
        )
        donor_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/donors/{donor_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted in database
        result = await db_session.execute(select(Donor).where(Donor.id == donor_id))
        donor = result.scalar_one_or_none()
        assert donor is None

