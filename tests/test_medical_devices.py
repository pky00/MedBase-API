import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.medical_device import MedicalDevice


class TestMedicalDeviceEndpoints:
    """Test cases for medical device endpoints."""

    @pytest.mark.asyncio
    async def test_create_medical_device(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new medical device."""
        device_data = {
            "name": "Standard Wheelchair",
            "code": "DEV001",
            "manufacturer": "MobilityPlus",
            "model": "WC-100",
            "size": "M",
            "is_reusable": True,
        }
        response = await client.post(
            "/api/v1/medical-devices/",
            json=device_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == device_data["name"]
        assert data["code"] == device_data["code"]

        # Verify in database
        result = await db_session.execute(select(MedicalDevice).where(MedicalDevice.id == data["id"]))
        device = result.scalar_one_or_none()
        assert device is not None

    @pytest.mark.asyncio
    async def test_create_medical_device_duplicate_code(self, client: AsyncClient, admin_headers: dict):
        """Test creating device with duplicate code fails."""
        device_data = {
            "name": "Device 1",
            "code": "DUPDEV001",
        }
        await client.post("/api/v1/medical-devices/", json=device_data, headers=admin_headers)

        device_data["name"] = "Device 2"
        response = await client.post("/api/v1/medical-devices/", json=device_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Device code already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_medical_devices(self, client: AsyncClient, admin_headers: dict):
        """Test listing medical devices."""
        response = await client.get("/api/v1/medical-devices/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_update_medical_device(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a medical device."""
        create_response = await client.post(
            "/api/v1/medical-devices/",
            json={"name": "Update Test Device"},
            headers=admin_headers,
        )
        device_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/medical-devices/{device_id}",
            json={"name": "Updated Device Name", "requires_fitting": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Device Name"
        assert response.json()["requires_fitting"] is True

    @pytest.mark.asyncio
    async def test_delete_medical_device(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a medical device."""
        create_response = await client.post(
            "/api/v1/medical-devices/",
            json={"name": "Delete Test Device"},
            headers=admin_headers,
        )
        device_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/medical-devices/{device_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(MedicalDevice).where(MedicalDevice.id == device_id))
        assert result.scalar_one_or_none() is None

