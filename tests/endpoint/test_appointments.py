"""Tests for appointment endpoints."""
from datetime import datetime, date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.appointment import Appointment
from app.model.patient import Patient
from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for testing."""
    tp = ThirdParty(name="Test Patient", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        date_of_birth=date(1990, 5, 15),
        gender="male",
        phone="1234567890",
        email="test.patient@test.com",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def doctor(db_session: AsyncSession, admin_user: User) -> Doctor:
    """Create a doctor for testing."""
    tp = ThirdParty(name="Dr. Test", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    doctor = Doctor(
        third_party_id=tp.id,
        name="Dr. Test",
        specialization="General",
        type="internal",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a referral partner for testing."""
    tp = ThirdParty(name="Test Partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        name="Test Partner",
        partner_type="referral",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def appointment(
    db_session: AsyncSession, admin_user: User,
    patient: Patient, doctor: Doctor,
) -> Appointment:
    """Create an appointment for testing."""
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime(2026, 3, 1, 10, 0, 0),
        status="scheduled",
        type="scheduled",
        location="internal",
        notes="Test appointment",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


@pytest.fixture
async def second_appointment(
    db_session: AsyncSession, admin_user: User,
    patient: Patient, doctor: Doctor,
) -> Appointment:
    """Create a second appointment for testing."""
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime(2026, 3, 2, 14, 0, 0),
        status="in_progress",
        type="walk_in",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)
    return appointment


class TestGetAppointments:
    """Tests for GET /api/v1/appointments"""

    @pytest.mark.asyncio
    async def test_get_appointments_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
    ):
        """Test getting appointments list."""
        response = await client.get("/api/v1/appointments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_appointments_unauthenticated(self, client: AsyncClient):
        """Test getting appointments without authentication."""
        response = await client.get("/api/v1/appointments")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_appointments_filter_by_status(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test filtering appointments by status."""
        response = await client.get(
            "/api/v1/appointments", params={"status": "scheduled"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "scheduled"

    @pytest.mark.asyncio
    async def test_get_appointments_filter_by_type(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test filtering appointments by type."""
        response = await client.get(
            "/api/v1/appointments", params={"type": "scheduled"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["type"] == "scheduled"

    @pytest.mark.asyncio
    async def test_get_appointments_filter_by_patient_id(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, patient: Patient,
    ):
        """Test filtering appointments by patient_id."""
        response = await client.get(
            "/api/v1/appointments", params={"patient_id": patient.id}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["patient_id"] == patient.id

    @pytest.mark.asyncio
    async def test_get_appointments_filter_by_location(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test filtering appointments by location."""
        response = await client.get(
            "/api/v1/appointments", params={"location": "internal"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["location"] == "internal"

    @pytest.mark.asyncio
    async def test_get_appointments_pagination(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, second_appointment: Appointment,
    ):
        """Test pagination works correctly."""
        response = await client.get(
            "/api/v1/appointments", params={"page": 1, "size": 1}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_appointments_includes_names(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test that list response includes patient and doctor names."""
        response = await client.get("/api/v1/appointments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        item = data["items"][0]
        assert "code" in item
        assert "patient_name" in item
        assert "doctor_name" in item


class TestGetAppointment:
    """Tests for GET /api/v1/appointments/{id}"""

    @pytest.mark.asyncio
    async def test_get_appointment_by_id(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test getting appointment by ID with details."""
        response = await client.get(
            f"/api/v1/appointments/{appointment.id}", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment.id
        assert "code" in data
        assert data["status"] == "scheduled"
        assert data["type"] == "scheduled"
        assert data["location"] == "internal"
        assert "patient_name" in data
        assert "doctor_name" in data
        assert "vital_signs" in data
        assert "medical_record" in data

    @pytest.mark.asyncio
    async def test_get_appointment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent appointment."""
        response = await client.get("/api/v1/appointments/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateAppointment:
    """Tests for POST /api/v1/appointments"""

    @pytest.mark.asyncio
    async def test_create_appointment_success(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, doctor: Doctor, db_session: AsyncSession,
    ):
        """Test creating an appointment."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "doctor_id": doctor.id,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "scheduled",
                "location": "internal",
                "notes": "Follow-up visit",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["doctor_id"] == doctor.id
        assert data["status"] == "scheduled"
        assert data["type"] == "scheduled"
        assert data["location"] == "internal"
        assert data["notes"] == "Follow-up visit"
        assert "code" in data
        assert len(data["code"]) == 6

        # Verify in database
        result = await db_session.execute(
            select(Appointment).where(Appointment.id == data["id"])
        )
        db_appt = result.scalar_one_or_none()
        assert db_appt is not None
        assert db_appt.patient_id == patient.id

    @pytest.mark.asyncio
    async def test_create_walk_in_appointment(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test creating a walk-in appointment."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "walk_in",
                "location": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "walk_in"
        assert data["doctor_id"] is None

    @pytest.mark.asyncio
    async def test_create_external_appointment_with_partner(
        self, client: AsyncClient, admin_headers: dict,
        patient: Patient, partner: Partner,
    ):
        """Test creating an external appointment with a partner."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "partner_id": partner.id,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "scheduled",
                "location": "external",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["location"] == "external"
        assert data["partner_id"] == partner.id

    @pytest.mark.asyncio
    async def test_create_external_appointment_without_partner_fails(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test that external appointments require a partner_id."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "scheduled",
                "location": "external",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "partner_id" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_patient(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating appointment with non-existent patient."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": 99999,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "scheduled",
                "location": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Patient not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_doctor(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test creating appointment with non-existent doctor."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "doctor_id": 99999,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "scheduled",
                "location": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Doctor not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_type(
        self, client: AsyncClient, admin_headers: dict, patient: Patient,
    ):
        """Test creating appointment with invalid type."""
        response = await client.post(
            "/api/v1/appointments",
            json={
                "patient_id": patient.id,
                "appointment_date": "2026-03-15T09:00:00",
                "type": "invalid",
                "location": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateAppointment:
    """Tests for PUT /api/v1/appointments/{id}"""

    @pytest.mark.asyncio
    async def test_update_appointment_success(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test updating an appointment."""
        response = await client.put(
            f"/api/v1/appointments/{appointment.id}",
            json={"notes": "Updated notes"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"

    @pytest.mark.asyncio
    async def test_update_appointment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent appointment."""
        response = await client.put(
            "/api/v1/appointments/99999", json={"notes": "Test"}, headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_completed_appointment_fails(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, appointment: Appointment,
    ):
        """Test that completed appointments cannot be updated."""
        # Mark appointment as completed
        appointment.status = "completed"
        await db_session.commit()

        response = await client.put(
            f"/api/v1/appointments/{appointment.id}",
            json={"notes": "Try update"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()


class TestUpdateAppointmentStatus:
    """Tests for PUT /api/v1/appointments/{id}/status"""

    @pytest.mark.asyncio
    async def test_update_status_success(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test updating appointment status."""
        response = await client.put(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "in_progress"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_update_status_to_completed(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test completing an appointment."""
        response = await client.put(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "completed"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating status of non-existent appointment."""
        response = await client.put(
            "/api/v1/appointments/99999/status",
            json={"status": "in_progress"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_invalid_value(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test updating status with invalid value."""
        response = await client.put(
            f"/api/v1/appointments/{appointment.id}/status",
            json={"status": "invalid_status"},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestDeleteAppointment:
    """Tests for DELETE /api/v1/appointments/{id}"""

    @pytest.mark.asyncio
    async def test_delete_appointment_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, appointment: Appointment,
    ):
        """Test deleting appointment (soft delete)."""
        appointment_id = appointment.id
        response = await client.delete(
            f"/api/v1/appointments/{appointment_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        db_appt = result.scalar_one_or_none()
        assert db_appt.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_appointment_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent appointment."""
        response = await client.delete("/api/v1/appointments/99999", headers=admin_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_deleted_appointment_not_in_list(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test that deleted appointment is not returned in list."""
        await client.delete(f"/api/v1/appointments/{appointment.id}", headers=admin_headers)

        response = await client.get("/api/v1/appointments", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        appointment_ids = [a["id"] for a in data["items"]]
        assert appointment.id not in appointment_ids
