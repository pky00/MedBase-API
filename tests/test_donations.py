import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy import select
from app.models.donation import Donation


class TestDonationEndpoints:
    """Test cases for donation endpoints."""

    async def _create_donor(self, client: AsyncClient, admin_headers: dict) -> str:
        """Helper to create a test donor."""
        import uuid
        response = await client.post(
            "/api/v1/donors/",
            json={
                "name": f"Test Donor {uuid.uuid4().hex[:8]}",
                "donor_type": "organization",
            },
            headers=admin_headers,
        )
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_donation(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new donation."""
        donor_id = await self._create_donor(client, admin_headers)

        donation_data = {
            "donor_id": donor_id,
            "donation_type": "medicine",
            "donation_date": str(date.today()),
            "total_items_count": 100,
            "notes": "Monthly medicine donation",
        }
        response = await client.post(
            "/api/v1/donations/",
            json=donation_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["donor_id"] == donor_id
        assert data["donation_type"] == "medicine"
        assert "donation_number" in data

        # Verify in database
        result = await db_session.execute(select(Donation).where(Donation.id == data["id"]))
        donation = result.scalar_one_or_none()
        assert donation is not None

    @pytest.mark.asyncio
    async def test_create_donation_invalid_donor(self, client: AsyncClient, admin_headers: dict):
        """Test creating donation with invalid donor fails."""
        fake_donor_id = "00000000-0000-0000-0000-000000000000"

        response = await client.post(
            "/api/v1/donations/",
            json={
                "donor_id": fake_donor_id,
                "donation_type": "equipment",
                "donation_date": str(date.today()),
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Donor not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_donations(self, client: AsyncClient, admin_headers: dict):
        """Test listing donations."""
        donor_id = await self._create_donor(client, admin_headers)
        await client.post(
            "/api/v1/donations/",
            json={
                "donor_id": donor_id,
                "donation_type": "mixed",
                "donation_date": str(date.today()),
            },
            headers=admin_headers,
        )

        response = await client.get("/api/v1/donations/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_donations_filter_by_type(self, client: AsyncClient, admin_headers: dict):
        """Test filtering donations by type."""
        donor_id = await self._create_donor(client, admin_headers)
        await client.post(
            "/api/v1/donations/",
            json={
                "donor_id": donor_id,
                "donation_type": "medical_device",
                "donation_date": str(date.today()),
            },
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/donations/?donation_type=medical_device",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for donation in data["data"]:
            assert donation["donation_type"] == "medical_device"

    @pytest.mark.asyncio
    async def test_update_donation(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a donation."""
        donor_id = await self._create_donor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/donations/",
            json={
                "donor_id": donor_id,
                "donation_type": "medicine",
                "donation_date": str(date.today()),
            },
            headers=admin_headers,
        )
        donation_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/donations/{donation_id}",
            json={"total_items_count": 50, "notes": "Updated notes"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["total_items_count"] == 50
        assert response.json()["notes"] == "Updated notes"

    @pytest.mark.asyncio
    async def test_delete_donation(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a donation."""
        donor_id = await self._create_donor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/donations/",
            json={
                "donor_id": donor_id,
                "donation_type": "equipment",
                "donation_date": str(date.today()),
            },
            headers=admin_headers,
        )
        donation_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/donations/{donation_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(Donation).where(Donation.id == donation_id))
        assert result.scalar_one_or_none() is None

