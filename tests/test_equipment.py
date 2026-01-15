import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.equipment import Equipment


class TestEquipmentEndpoints:
    """Test cases for equipment endpoints."""

    @pytest.mark.asyncio
    async def test_create_equipment(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating new equipment."""
        equipment_data = {
            "name": "Blood Pressure Monitor",
            "asset_code": "EQ001",
            "model": "BP-100",
            "manufacturer": "MedEquip",
            "equipment_condition": "new",
        }
        response = await client.post(
            "/api/v1/equipment/",
            json=equipment_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == equipment_data["name"]
        assert data["asset_code"] == equipment_data["asset_code"]

        # Verify in database
        result = await db_session.execute(select(Equipment).where(Equipment.id == data["id"]))
        equipment = result.scalar_one_or_none()
        assert equipment is not None

    @pytest.mark.asyncio
    async def test_create_equipment_duplicate_asset_code(self, client: AsyncClient, admin_headers: dict):
        """Test creating equipment with duplicate asset code fails."""
        equipment_data = {
            "name": "Equipment 1",
            "asset_code": "DUPEQ001",
        }
        await client.post("/api/v1/equipment/", json=equipment_data, headers=admin_headers)

        equipment_data["name"] = "Equipment 2"
        response = await client.post("/api/v1/equipment/", json=equipment_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Asset code already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_equipment(self, client: AsyncClient, admin_headers: dict):
        """Test listing equipment."""
        response = await client.get("/api/v1/equipment/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_equipment_filter_by_donation(self, client: AsyncClient, admin_headers: dict):
        """Test filtering equipment by donation status."""
        await client.post(
            "/api/v1/equipment/",
            json={"name": "Donated Equipment", "is_donation": True},
            headers=admin_headers,
        )

        response = await client.get("/api/v1/equipment/?is_donation=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        for eq in data["data"]:
            assert eq["is_donation"] is True

    @pytest.mark.asyncio
    async def test_update_equipment(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating equipment."""
        create_response = await client.post(
            "/api/v1/equipment/",
            json={"name": "Update Test Equipment"},
            headers=admin_headers,
        )
        equipment_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/equipment/{equipment_id}",
            json={"equipment_condition": "needs_repair", "is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["equipment_condition"] == "needs_repair"
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_equipment(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting equipment."""
        create_response = await client.post(
            "/api/v1/equipment/",
            json={"name": "Delete Test Equipment"},
            headers=admin_headers,
        )
        equipment_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/equipment/{equipment_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(Equipment).where(Equipment.id == equipment_id))
        assert result.scalar_one_or_none() is None

