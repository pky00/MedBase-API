"""Tests for dashboard statistics endpoints."""
from datetime import datetime, date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.appointment import Appointment
from app.model.inventory import Inventory
from app.model.inventory_transaction import InventoryTransaction
from app.model.inventory_transaction_item import InventoryTransactionItem
from app.model.medicine import Medicine
from app.model.medicine_category import MedicineCategory
from app.model.equipment import Equipment
from app.model.equipment_category import EquipmentCategory
from app.model.partner import Partner
from app.model.doctor import Doctor
from app.model.patient import Patient
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def dashboard_data(db_session: AsyncSession, admin_user: User):
    """Create sample data for dashboard tests."""
    # Create patients
    tp1 = ThirdParty(name="Patient One", type="patient", is_active=True)
    tp2 = ThirdParty(name="Patient Two", type="patient", is_active=True)
    db_session.add_all([tp1, tp2])
    await db_session.flush()

    patient1 = Patient(
        third_party_id=tp1.id, first_name="Patient", last_name="One",
        gender="male", is_active=True,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    patient2 = Patient(
        third_party_id=tp2.id, first_name="Patient", last_name="Two",
        gender="female", is_active=True,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add_all([patient1, patient2])
    await db_session.flush()

    # Create a doctor
    tp_doc = ThirdParty(name="Dr. Stats", type="doctor", is_active=True)
    db_session.add(tp_doc)
    await db_session.flush()
    doctor = Doctor(
        third_party_id=tp_doc.id, name="Dr. Stats",
        specialization="General", type="internal", is_active=True,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(doctor)
    await db_session.flush()

    # Create a partner
    tp_partner = ThirdParty(name="Stats Hospital", type="partner", is_active=True)
    db_session.add(tp_partner)
    await db_session.flush()
    partner = Partner(
        third_party_id=tp_partner.id, name="Stats Hospital",
        partner_type="both", organization_type="hospital", is_active=True,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.flush()

    # Create appointments
    today = datetime.now()
    appt1 = Appointment(
        patient_id=patient1.id, doctor_id=doctor.id,
        appointment_date=today,
        status="scheduled", type="scheduled", location="internal",
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    appt2 = Appointment(
        patient_id=patient2.id,
        appointment_date=today + timedelta(days=7),
        status="scheduled", type="walk_in", location="internal",
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    appt3 = Appointment(
        patient_id=patient1.id,
        appointment_date=today - timedelta(days=10),
        status="completed", type="scheduled", location="internal",
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add_all([appt1, appt2, appt3])
    await db_session.flush()

    # Create inventory items
    med_cat = MedicineCategory(
        name="Stats Cat", created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(med_cat)
    await db_session.flush()

    medicine = Medicine(
        name="Stats Medicine", category_id=med_cat.id, unit="tablets",
        is_active=True, created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(medicine)
    await db_session.flush()

    inv1 = Inventory(
        item_type="medicine", item_id=medicine.id, quantity=5,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(inv1)
    await db_session.flush()

    equip_cat = EquipmentCategory(
        name="Stats Equip Cat", created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(equip_cat)
    await db_session.flush()

    equip = Equipment(
        name="Stats Equipment", category_id=equip_cat.id, condition="new",
        is_active=True, created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(equip)
    await db_session.flush()

    inv2 = Inventory(
        item_type="equipment", item_id=equip.id, quantity=50,
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(inv2)
    await db_session.flush()

    # Create a transaction
    txn = InventoryTransaction(
        transaction_type="purchase",
        third_party_id=admin_user.third_party_id,
        transaction_date=date.today(),
        notes="Stats test purchase",
        created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(txn)
    await db_session.flush()

    txn_item = InventoryTransactionItem(
        transaction_id=txn.id, item_type="medicine", item_id=medicine.id,
        quantity=20, created_by=admin_user.username, updated_by=admin_user.username,
    )
    db_session.add(txn_item)
    await db_session.commit()

    return {
        "patients": [patient1, patient2],
        "doctor": doctor,
        "partner": partner,
        "appointments": [appt1, appt2, appt3],
        "inventories": [inv1, inv2],
        "transaction": txn,
    }


class TestSummaryStats:
    """Tests for GET /api/v1/statistics/summary"""

    @pytest.mark.asyncio
    async def test_get_summary_authenticated(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test getting summary statistics."""
        response = await client.get("/api/v1/statistics/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_patients"] >= 2
        assert data["total_appointments"] >= 3
        assert data["total_inventory_items"] >= 2
        assert data["total_transactions"] >= 1
        assert data["total_partners"] >= 1
        assert data["total_doctors"] >= 1
        assert data["active_patients"] >= 2
        assert data["active_partners"] >= 1
        assert data["active_doctors"] >= 1

    @pytest.mark.asyncio
    async def test_get_summary_unauthenticated(self, client: AsyncClient):
        """Test getting summary without authentication."""
        response = await client.get("/api/v1/statistics/summary")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_summary_empty_db(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test summary with empty database returns zeros."""
        response = await client.get("/api/v1/statistics/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_patients"] == 0
        assert data["total_appointments"] == 0


class TestInventoryStats:
    """Tests for GET /api/v1/statistics/inventory"""

    @pytest.mark.asyncio
    async def test_get_inventory_stats(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test getting inventory statistics."""
        response = await client.get("/api/v1/statistics/inventory", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] >= 2
        assert data["total_quantity"] >= 55
        assert "low_stock_items" in data
        assert "items_by_type" in data
        assert len(data["items_by_type"]) >= 2

    @pytest.mark.asyncio
    async def test_inventory_stats_low_stock(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test that low stock items are detected (threshold = 10)."""
        response = await client.get("/api/v1/statistics/inventory", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Medicine with qty=5 should be in low stock
        low_stock_names = [item["item_name"] for item in data["low_stock_items"]]
        assert "Stats Medicine" in low_stock_names

    @pytest.mark.asyncio
    async def test_inventory_stats_unauthenticated(self, client: AsyncClient):
        """Test getting inventory stats without authentication."""
        response = await client.get("/api/v1/statistics/inventory")
        assert response.status_code == 401


class TestAppointmentStats:
    """Tests for GET /api/v1/statistics/appointments"""

    @pytest.mark.asyncio
    async def test_get_appointment_stats(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test getting appointment statistics."""
        response = await client.get("/api/v1/statistics/appointments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "today_count" in data
        assert "upcoming_count" in data
        assert "by_status" in data
        assert "by_month" in data
        assert data["today_count"] >= 1  # We created one today
        assert data["upcoming_count"] >= 1  # We created one future
        assert data["total_completed"] >= 1  # We created one completed

    @pytest.mark.asyncio
    async def test_appointment_stats_by_status(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test that status breakdown is correct."""
        response = await client.get("/api/v1/statistics/appointments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        statuses = {s["status"]: s["count"] for s in data["by_status"]}
        assert statuses.get("scheduled", 0) >= 2
        assert statuses.get("completed", 0) >= 1

    @pytest.mark.asyncio
    async def test_appointment_stats_unauthenticated(self, client: AsyncClient):
        """Test getting appointment stats without authentication."""
        response = await client.get("/api/v1/statistics/appointments")
        assert response.status_code == 401


class TestTransactionStats:
    """Tests for GET /api/v1/statistics/transactions"""

    @pytest.mark.asyncio
    async def test_get_transaction_stats(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test getting transaction statistics."""
        response = await client.get("/api/v1/statistics/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] >= 1
        assert "by_type" in data
        assert "recent_transactions" in data
        assert len(data["recent_transactions"]) >= 1

    @pytest.mark.asyncio
    async def test_transaction_stats_by_type(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test that type breakdown is correct."""
        response = await client.get("/api/v1/statistics/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        types = {t["transaction_type"]: t for t in data["by_type"]}
        assert "purchase" in types
        assert types["purchase"]["count"] >= 1

    @pytest.mark.asyncio
    async def test_transaction_stats_recent(
        self, client: AsyncClient, admin_headers: dict, dashboard_data,
    ):
        """Test that recent transactions include third party name and item count."""
        response = await client.get("/api/v1/statistics/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        recent = data["recent_transactions"]
        assert len(recent) >= 1
        assert "third_party_name" in recent[0]
        assert "item_count" in recent[0]
        assert recent[0]["item_count"] >= 1

    @pytest.mark.asyncio
    async def test_transaction_stats_unauthenticated(self, client: AsyncClient):
        """Test getting transaction stats without authentication."""
        response = await client.get("/api/v1/statistics/transactions")
        assert response.status_code == 401
