"""Tests for medical device endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medical_device import MedicalDevice
from app.model.medical_device_category import MedicalDeviceCategory
from app.model.inventory import Inventory
from app.model.user import User


@pytest.fixture
async def device_category(db_session: AsyncSession, admin_user: User) -> MedicalDeviceCategory:
    """Create a medical device category for testing."""
    cat = MedicalDeviceCategory(
        name="Monitors",
        description="Patient monitoring devices",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


class TestGetMedicalDevices:
    """Tests for GET /api/v1/medical-devices"""

    @pytest.mark.asyncio
    async def test_get_devices_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting medical devices list."""
        response = await client.get("/api/v1/medical-devices", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_devices_unauthenticated(self, client: AsyncClient):
        """Test getting devices without authentication."""
        response = await client.get("/api/v1/medical-devices")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_devices_with_category_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, device_category: MedicalDeviceCategory
    ):
        """Test filtering devices by category."""
        dev = MedicalDevice(
            name="BP Monitor", category_id=device_category.id,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(dev)
        await db_session.commit()

        response = await client.get(
            "/api/v1/medical-devices",
            params={"category_id": device_category.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["category_id"] == device_category.id

    @pytest.mark.asyncio
    async def test_get_devices_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test searching medical devices."""
        d1 = MedicalDevice(name="Blood Pressure Monitor", created_by=admin_user.username, updated_by=admin_user.username)
        d2 = MedicalDevice(name="Pulse Oximeter", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([d1, d2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/medical-devices",
            params={"search": "Blood"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Blood Pressure Monitor"


class TestGetMedicalDevice:
    """Tests for GET /api/v1/medical-devices/{id}"""

    @pytest.mark.asyncio
    async def test_get_device_with_details(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, device_category: MedicalDeviceCategory
    ):
        """Test getting device by ID includes inventory and category."""
        response = await client.post(
            "/api/v1/medical-devices",
            json={
                "name": "Heart Monitor",
                "category_id": device_category.id,
                "serial_number": "HM-001",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        device_id = response.json()["id"]

        response = await client.get(
            f"/api/v1/medical-devices/{device_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Heart Monitor"
        assert data["category_name"] == "Monitors"
        assert data["inventory_quantity"] == 0
        assert data["serial_number"] == "HM-001"

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent device."""
        response = await client.get(
            "/api/v1/medical-devices/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateMedicalDevice:
    """Tests for POST /api/v1/medical-devices"""

    @pytest.mark.asyncio
    async def test_create_device_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, device_category: MedicalDeviceCategory
    ):
        """Test creating a medical device and verify database state."""
        device_data = {
            "name": "ECG Machine",
            "category_id": device_category.id,
            "description": "12-lead ECG",
            "serial_number": "ECG-001",
            "is_active": True,
        }

        response = await client.post(
            "/api/v1/medical-devices",
            json=device_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ECG Machine"
        assert data["serial_number"] == "ECG-001"

        # Verify in database
        result = await db_session.execute(
            select(MedicalDevice).where(MedicalDevice.id == data["id"])
        )
        db_dev = result.scalar_one_or_none()
        assert db_dev is not None
        assert db_dev.name == "ECG Machine"
        assert db_dev.created_by == admin_user.username

        # Verify inventory auto-created
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medical_device",
                Inventory.item_id == data["id"],
            )
        )
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.quantity == 0

    @pytest.mark.asyncio
    async def test_create_device_without_category(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating device without a category."""
        response = await client.post(
            "/api/v1/medical-devices",
            json={"name": "Generic Device"},
            headers=admin_headers,
        )

        assert response.status_code == 201
        assert response.json()["category_id"] is None

    @pytest.mark.asyncio
    async def test_create_device_invalid_category(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test creating device with non-existent category."""
        response = await client.post(
            "/api/v1/medical-devices",
            json={"name": "Test Device", "category_id": 99999},
            headers=admin_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_device_duplicate_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating device with duplicate name fails."""
        dev = MedicalDevice(name="Duplicate Device", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(dev)
        await db_session.commit()

        response = await client.post(
            "/api/v1/medical-devices",
            json={"name": "Duplicate Device"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateMedicalDevice:
    """Tests for PUT /api/v1/medical-devices/{id}"""

    @pytest.mark.asyncio
    async def test_update_device_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating a medical device and verify in database."""
        admin_username = admin_user.username
        dev = MedicalDevice(
            name="Old Name", serial_number="OLD-001",
            created_by=admin_username, updated_by=admin_username,
        )
        db_session.add(dev)
        await db_session.commit()
        await db_session.refresh(dev)
        dev_id = dev.id

        response = await client.put(
            f"/api/v1/medical-devices/{dev_id}",
            json={"name": "New Name", "serial_number": "NEW-001"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["serial_number"] == "NEW-001"

        # Verify database
        db_session.expire_all()
        result = await db_session.execute(
            select(MedicalDevice).where(MedicalDevice.id == dev_id)
        )
        db_dev = result.scalar_one_or_none()
        assert db_dev.name == "New Name"
        assert db_dev.updated_by == admin_username

    @pytest.mark.asyncio
    async def test_update_device_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent device."""
        response = await client.put(
            "/api/v1/medical-devices/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestDeleteMedicalDevice:
    """Tests for DELETE /api/v1/medical-devices/{id}"""

    @pytest.mark.asyncio
    async def test_delete_device_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting a medical device when inventory is 0."""
        response = await client.post(
            "/api/v1/medical-devices",
            json={"name": "To Delete", "serial_number": "DEL-001"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        dev_id = response.json()["id"]

        response = await client.delete(
            f"/api/v1/medical-devices/{dev_id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(MedicalDevice).where(MedicalDevice.id == dev_id)
        )
        db_dev = result.scalar_one_or_none()
        assert db_dev.is_deleted is True

        # Verify inventory also soft deleted
        result = await db_session.execute(
            select(Inventory).where(
                Inventory.item_type == "medical_device",
                Inventory.item_id == dev_id,
            )
        )
        inv = result.scalar_one_or_none()
        assert inv.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_device_with_inventory(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test cannot delete device when inventory quantity > 0."""
        dev = MedicalDevice(name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(dev)
        await db_session.flush()
        await db_session.refresh(dev)

        inv = Inventory(
            item_type="medical_device", item_id=dev.id, quantity=3,
            created_by=admin_user.username, updated_by=admin_user.username,
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/medical-devices/{dev.id}", headers=admin_headers
        )

        assert response.status_code == 400
        assert "inventory quantity" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_device_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent device."""
        response = await client.delete(
            "/api/v1/medical-devices/99999", headers=admin_headers
        )
        assert response.status_code == 404
