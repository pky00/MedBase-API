"""Tests for medical device endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.medical_device import MedicalDevice
from app.model.medical_device_category import MedicalDeviceCategory
from app.model.inventory import Inventory
from app.model.item import Item
from app.model.user import User


@pytest.fixture
async def device_category(db_session: AsyncSession, admin_user: User) -> MedicalDeviceCategory:
    cat = MedicalDeviceCategory(name="Monitors", description="Patient monitoring devices", created_by=admin_user.username, updated_by=admin_user.username)
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


class TestGetMedicalDevices:
    @pytest.mark.asyncio
    async def test_get_devices_authenticated(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        response = await client.get("/api/v1/medical-devices", headers=admin_headers)
        assert response.status_code == 200
        assert "items" in response.json()

    @pytest.mark.asyncio
    async def test_get_devices_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/medical-devices")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_devices_with_category_filter(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession, device_category: MedicalDeviceCategory):
        item = Item(item_type="medical_device", name="BP Monitor", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        dev = MedicalDevice(item_id=item.id, code="MD-BPM", name="BP Monitor", category_id=device_category.id, created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(dev)
        await db_session.commit()

        response = await client.get("/api/v1/medical-devices", params={"category_id": device_category.id}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_devices_with_search(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession):
        item1 = Item(item_type="medical_device", name="Blood Pressure Monitor", created_by=admin_user.username, updated_by=admin_user.username)
        item2 = Item(item_type="medical_device", name="Pulse Oximeter", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([item1, item2])
        await db_session.flush()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        d1 = MedicalDevice(item_id=item1.id, code="MD-BP1", name="Blood Pressure Monitor", created_by=admin_user.username, updated_by=admin_user.username)
        d2 = MedicalDevice(item_id=item2.id, code="MD-POX", name="Pulse Oximeter", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add_all([d1, d2])
        await db_session.commit()

        response = await client.get("/api/v1/medical-devices", params={"search": "Blood"}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert response.json()["items"][0]["name"] == "Blood Pressure Monitor"


class TestGetMedicalDevice:
    @pytest.mark.asyncio
    async def test_get_device_with_details(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession, device_category: MedicalDeviceCategory):
        response = await client.post("/api/v1/medical-devices", json={"code": "MD-HRM", "name": "Heart Monitor", "category_id": device_category.id, "serial_number": "HM-001"}, headers=admin_headers)
        assert response.status_code == 201
        device_id = response.json()["id"]

        response = await client.get(f"/api/v1/medical-devices/{device_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Heart Monitor"
        assert data["category"]["name"] == "Monitors"
        assert data["inventory_quantity"] == 0
        assert "item_id" in data

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.get("/api/v1/medical-devices/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateMedicalDevice:
    @pytest.mark.asyncio
    async def test_create_device_success(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession, device_category: MedicalDeviceCategory):
        response = await client.post("/api/v1/medical-devices", json={"code": "MD-ECG", "name": "ECG Machine", "category_id": device_category.id, "description": "12-lead ECG", "serial_number": "ECG-001", "is_active": True}, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ECG Machine"
        assert "item_id" in data

        result = await db_session.execute(select(MedicalDevice).where(MedicalDevice.id == data["id"]))
        db_dev = result.scalar_one_or_none()
        assert db_dev is not None
        assert db_dev.item_id is not None

        result = await db_session.execute(select(Inventory).where(Inventory.item_id == db_dev.item_id))
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.quantity == 0

    @pytest.mark.asyncio
    async def test_create_device_without_category(self, client: AsyncClient, admin_headers: dict):
        response = await client.post("/api/v1/medical-devices", json={"code": "MD-GEN", "name": "Generic Device"}, headers=admin_headers)
        assert response.status_code == 201
        assert response.json()["category_id"] is None

    @pytest.mark.asyncio
    async def test_create_device_invalid_category(self, client: AsyncClient, admin_headers: dict):
        response = await client.post("/api/v1/medical-devices", json={"code": "MD-TST", "name": "Test Device", "category_id": 99999}, headers=admin_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_device_duplicate_name(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession):
        item = Item(item_type="medical_device", name="Duplicate Device", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        dev = MedicalDevice(item_id=item.id, code="MD-DUP", name="Duplicate Device", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(dev)
        await db_session.commit()

        response = await client.post("/api/v1/medical-devices", json={"code": "MD-DU2", "name": "Duplicate Device"}, headers=admin_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestUpdateMedicalDevice:
    @pytest.mark.asyncio
    async def test_update_device_success(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession):
        admin_username = admin_user.username
        item = Item(item_type="medical_device", name="Old Name", created_by=admin_username, updated_by=admin_username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        dev = MedicalDevice(item_id=item.id, code="MD-OLD", name="Old Name", serial_number="OLD-001", created_by=admin_username, updated_by=admin_username)
        db_session.add(dev)
        await db_session.commit()
        await db_session.refresh(dev)

        response = await client.put(f"/api/v1/medical-devices/{dev.id}", json={"name": "New Name", "serial_number": "NEW-001"}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_device_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.put("/api/v1/medical-devices/99999", json={"name": "Test"}, headers=admin_headers)
        assert response.status_code == 404


class TestDeleteMedicalDevice:
    @pytest.mark.asyncio
    async def test_delete_device_success(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession):
        response = await client.post("/api/v1/medical-devices", json={"code": "MD-DEL", "name": "To Delete", "serial_number": "DEL-001"}, headers=admin_headers)
        assert response.status_code == 201
        dev_id = response.json()["id"]
        item_id = response.json()["item_id"]

        response = await client.delete(f"/api/v1/medical-devices/{dev_id}", headers=admin_headers)
        assert response.status_code == 200

        db_session.expire_all()
        result = await db_session.execute(select(Inventory).where(Inventory.item_id == item_id))
        inv = result.scalar_one_or_none()
        assert inv.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_device_with_inventory(self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession):
        item = Item(item_type="medical_device", name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        dev = MedicalDevice(item_id=item.id, code="MD-STK", name="Has Stock", created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(dev)
        await db_session.flush()
        await db_session.refresh(dev)

        inv = Inventory(item_id=item.id, quantity=3, created_by=admin_user.username, updated_by=admin_user.username)
        db_session.add(inv)
        await db_session.commit()

        response = await client.delete(f"/api/v1/medical-devices/{dev.id}", headers=admin_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_device_not_found(self, client: AsyncClient, admin_headers: dict):
        response = await client.delete("/api/v1/medical-devices/99999", headers=admin_headers)
        assert response.status_code == 404
