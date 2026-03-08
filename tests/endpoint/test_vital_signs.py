"""Tests for vital signs endpoints."""
from datetime import datetime, date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.appointment import Appointment
from app.model.vital_sign import VitalSign
from app.model.patient import Patient
from app.model.doctor import Doctor
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for testing."""
    tp = ThirdParty(name="VS Patient", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        gender="male",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def appointment(
    db_session: AsyncSession, admin_user: User, patient: Patient,
) -> Appointment:
    """Create an appointment for testing."""
    appointment = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 3, 1, 10, 0, 0),
        status="scheduled",
        type="scheduled",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
async def completed_appointment(
    db_session: AsyncSession, admin_user: User, patient: Patient,
) -> Appointment:
    """Create a completed appointment for testing."""
    appointment = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 2, 28, 10, 0, 0),
        status="completed",
        type="scheduled",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
async def vital_signs(
    db_session: AsyncSession, admin_user: User, appointment: Appointment,
) -> VitalSign:
    """Create vital signs for testing."""
    vs = VitalSign(
        appointment_id=appointment.id,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        heart_rate=72,
        temperature=36.6,
        respiratory_rate=16,
        weight=70.5,
        height=175.0,
        notes="Normal vitals",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(vs)
    await db_session.commit()
    await db_session.refresh(vs)
    return vs


class TestGetVitals:
    """Tests for GET /api/v1/appointments/{appointment_id}/vitals"""

    @pytest.mark.asyncio
    async def test_get_vitals_success(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, vital_signs: VitalSign,
    ):
        """Test getting vital signs for appointment."""
        response = await client.get(
            f"/api/v1/appointments/{appointment.id}/vitals", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["blood_pressure_systolic"] == 120
        assert data["blood_pressure_diastolic"] == 80
        assert data["heart_rate"] == 72
        assert data["appointment_id"] == appointment.id

    @pytest.mark.asyncio
    async def test_get_vitals_no_vitals(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test getting vitals when none exist."""
        response = await client.get(
            f"/api/v1/appointments/{appointment.id}/vitals", headers=admin_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_vitals_appointment_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test getting vitals for non-existent appointment."""
        response = await client.get(
            "/api/v1/appointments/99999/vitals", headers=admin_headers,
        )
        assert response.status_code == 404


class TestCreateVitals:
    """Tests for POST /api/v1/appointments/{appointment_id}/vitals"""

    @pytest.mark.asyncio
    async def test_create_vitals_success(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, db_session: AsyncSession,
    ):
        """Test creating vital signs for appointment."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/vitals",
            json={
                "blood_pressure_systolic": 130,
                "blood_pressure_diastolic": 85,
                "heart_rate": 78,
                "temperature": 37.0,
                "respiratory_rate": 18,
                "weight": 80.0,
                "height": 180.0,
                "notes": "Slightly elevated BP",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["blood_pressure_systolic"] == 130
        assert data["heart_rate"] == 78
        assert data["appointment_id"] == appointment.id

        # Verify in database
        result = await db_session.execute(
            select(VitalSign).where(VitalSign.id == data["id"])
        )
        db_vs = result.scalar_one_or_none()
        assert db_vs is not None
        assert db_vs.blood_pressure_systolic == 130

    @pytest.mark.asyncio
    async def test_create_vitals_all_optional(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test creating vital signs with only some fields."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/vitals",
            json={"heart_rate": 65},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["heart_rate"] == 65
        assert data["blood_pressure_systolic"] is None
        assert data["weight"] is None

    @pytest.mark.asyncio
    async def test_create_vitals_duplicate_fails(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, vital_signs: VitalSign,
    ):
        """Test that creating duplicate vitals for appointment fails."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/vitals",
            json={"heart_rate": 80},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exist" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_vitals_completed_appointment_fails(
        self, client: AsyncClient, admin_headers: dict,
        completed_appointment: Appointment,
    ):
        """Test that cannot add vitals to completed appointment."""
        response = await client.post(
            f"/api/v1/appointments/{completed_appointment.id}/vitals",
            json={"heart_rate": 72},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_vitals_appointment_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating vitals for non-existent appointment."""
        response = await client.post(
            "/api/v1/appointments/99999/vitals",
            json={"heart_rate": 72},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestUpdateVitals:
    """Tests for PUT /api/v1/vital-signs/{id}"""

    @pytest.mark.asyncio
    async def test_update_vitals_success(
        self, client: AsyncClient, admin_headers: dict, vital_signs: VitalSign,
    ):
        """Test updating vital signs."""
        response = await client.put(
            f"/api/v1/vital-signs/{vital_signs.id}",
            json={"heart_rate": 85, "notes": "After exercise"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["heart_rate"] == 85
        assert data["notes"] == "After exercise"

    @pytest.mark.asyncio
    async def test_update_vitals_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent vital signs."""
        response = await client.put(
            "/api/v1/vital-signs/99999",
            json={"heart_rate": 80},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_vitals_completed_appointment_fails(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, vital_signs: VitalSign, appointment: Appointment,
    ):
        """Test that cannot update vitals of completed appointment."""
        appointment.status = "completed"
        await db_session.commit()

        response = await client.put(
            f"/api/v1/vital-signs/{vital_signs.id}",
            json={"heart_rate": 90},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()


class TestDeleteVitals:
    """Tests for DELETE /api/v1/vital-signs/{id}"""

    @pytest.mark.asyncio
    async def test_delete_vitals_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, vital_signs: VitalSign,
    ):
        """Test deleting vital signs (soft delete)."""
        vs_id = vital_signs.id
        response = await client.delete(
            f"/api/v1/vital-signs/{vs_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(VitalSign).where(VitalSign.id == vs_id)
        )
        db_vs = result.scalar_one_or_none()
        assert db_vs.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_vitals_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent vital signs."""
        response = await client.delete("/api/v1/vital-signs/99999", headers=admin_headers)
        assert response.status_code == 404
