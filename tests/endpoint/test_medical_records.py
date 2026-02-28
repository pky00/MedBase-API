"""Tests for medical record endpoints."""
from datetime import datetime, date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.appointment import Appointment
from app.model.medical_record import MedicalRecord
from app.model.patient import Patient
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def patient(db_session: AsyncSession, admin_user: User) -> Patient:
    """Create a patient for testing."""
    tp = ThirdParty(name="MR Patient", type="patient", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    patient = Patient(
        third_party_id=tp.id,
        first_name="MR",
        last_name="Patient",
        gender="female",
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
    appt = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 3, 1, 10, 0, 0),
        status="in_progress",
        type="scheduled",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest.fixture
async def second_appointment(
    db_session: AsyncSession, admin_user: User, patient: Patient,
) -> Appointment:
    """Create a second appointment for testing."""
    appt = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 3, 5, 14, 0, 0),
        status="scheduled",
        type="walk_in",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest.fixture
async def completed_appointment(
    db_session: AsyncSession, admin_user: User, patient: Patient,
) -> Appointment:
    """Create a completed appointment for testing."""
    appt = Appointment(
        patient_id=patient.id,
        appointment_date=datetime(2026, 2, 28, 10, 0, 0),
        status="completed",
        type="scheduled",
        location="internal",
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(appt)
    await db_session.commit()
    await db_session.refresh(appt)
    return appt


@pytest.fixture
async def medical_record(
    db_session: AsyncSession, admin_user: User, appointment: Appointment,
) -> MedicalRecord:
    """Create a medical record for testing."""
    record = MedicalRecord(
        appointment_id=appointment.id,
        chief_complaint="Headache and dizziness",
        diagnosis="Tension headache",
        treatment_notes="Prescribed rest and analgesics",
        follow_up_date=date(2026, 3, 15),
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)
    return record


class TestGetMedicalRecords:
    """Tests for GET /api/v1/medical-records"""

    @pytest.mark.asyncio
    async def test_get_medical_records_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
    ):
        """Test getting medical records list."""
        response = await client.get("/api/v1/medical-records", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_medical_records_unauthenticated(self, client: AsyncClient):
        """Test getting medical records without authentication."""
        response = await client.get("/api/v1/medical-records")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_medical_records_filter_by_patient(
        self, client: AsyncClient, admin_headers: dict,
        medical_record: MedicalRecord, patient: Patient,
    ):
        """Test filtering medical records by patient_id."""
        response = await client.get(
            "/api/v1/medical-records",
            params={"patient_id": patient.id},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_medical_records_filter_by_appointment(
        self, client: AsyncClient, admin_headers: dict,
        medical_record: MedicalRecord, appointment: Appointment,
    ):
        """Test filtering medical records by appointment_id."""
        response = await client.get(
            "/api/v1/medical-records",
            params={"appointment_id": appointment.id},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_medical_records_includes_patient_name(
        self, client: AsyncClient, admin_headers: dict,
        medical_record: MedicalRecord,
    ):
        """Test that list response includes patient_name."""
        response = await client.get("/api/v1/medical-records", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        item = data["items"][0]
        assert "patient_name" in item


class TestGetMedicalRecord:
    """Tests for GET /api/v1/medical-records/{id}"""

    @pytest.mark.asyncio
    async def test_get_medical_record_by_id(
        self, client: AsyncClient, admin_headers: dict, medical_record: MedicalRecord,
    ):
        """Test getting medical record by ID."""
        response = await client.get(
            f"/api/v1/medical-records/{medical_record.id}", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chief_complaint"] == "Headache and dizziness"
        assert data["diagnosis"] == "Tension headache"
        assert data["follow_up_date"] == "2026-03-15"
        assert "patient_name" in data

    @pytest.mark.asyncio
    async def test_get_medical_record_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent medical record."""
        response = await client.get("/api/v1/medical-records/99999", headers=admin_headers)
        assert response.status_code == 404


class TestGetMedicalRecordForAppointment:
    """Tests for GET /api/v1/appointments/{appointment_id}/medical-record"""

    @pytest.mark.asyncio
    async def test_get_record_for_appointment(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, medical_record: MedicalRecord,
    ):
        """Test getting medical record for appointment."""
        response = await client.get(
            f"/api/v1/appointments/{appointment.id}/medical-record", headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["appointment_id"] == appointment.id

    @pytest.mark.asyncio
    async def test_get_record_no_record(
        self, client: AsyncClient, admin_headers: dict,
        second_appointment: Appointment,
    ):
        """Test getting record when none exists."""
        response = await client.get(
            f"/api/v1/appointments/{second_appointment.id}/medical-record",
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_record_appointment_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test getting record for non-existent appointment."""
        response = await client.get(
            "/api/v1/appointments/99999/medical-record", headers=admin_headers,
        )
        assert response.status_code == 404


class TestCreateMedicalRecord:
    """Tests for POST /api/v1/appointments/{appointment_id}/medical-record"""

    @pytest.mark.asyncio
    async def test_create_record_success(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, db_session: AsyncSession,
    ):
        """Test creating a medical record for appointment."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/medical-record",
            json={
                "chief_complaint": "Chest pain",
                "diagnosis": "Muscle strain",
                "treatment_notes": "Rest and NSAIDs",
                "follow_up_date": "2026-04-01",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["chief_complaint"] == "Chest pain"
        assert data["diagnosis"] == "Muscle strain"
        assert data["appointment_id"] == appointment.id

        # Verify in database
        result = await db_session.execute(
            select(MedicalRecord).where(MedicalRecord.id == data["id"])
        )
        db_record = result.scalar_one_or_none()
        assert db_record is not None
        assert db_record.chief_complaint == "Chest pain"

    @pytest.mark.asyncio
    async def test_create_record_minimal(
        self, client: AsyncClient, admin_headers: dict, appointment: Appointment,
    ):
        """Test creating a medical record with minimal fields."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/medical-record",
            json={"chief_complaint": "Fever"},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["chief_complaint"] == "Fever"
        assert data["diagnosis"] is None

    @pytest.mark.asyncio
    async def test_create_record_duplicate_fails(
        self, client: AsyncClient, admin_headers: dict,
        appointment: Appointment, medical_record: MedicalRecord,
    ):
        """Test that creating duplicate record for appointment fails."""
        response = await client.post(
            f"/api/v1/appointments/{appointment.id}/medical-record",
            json={"chief_complaint": "Another issue"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_record_completed_appointment_fails(
        self, client: AsyncClient, admin_headers: dict,
        completed_appointment: Appointment,
    ):
        """Test that cannot add record to completed appointment."""
        response = await client.post(
            f"/api/v1/appointments/{completed_appointment.id}/medical-record",
            json={"chief_complaint": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_record_appointment_not_found(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating record for non-existent appointment."""
        response = await client.post(
            "/api/v1/appointments/99999/medical-record",
            json={"chief_complaint": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404


class TestUpdateMedicalRecord:
    """Tests for PUT /api/v1/medical-records/{id}"""

    @pytest.mark.asyncio
    async def test_update_record_success(
        self, client: AsyncClient, admin_headers: dict, medical_record: MedicalRecord,
    ):
        """Test updating a medical record."""
        response = await client.put(
            f"/api/v1/medical-records/{medical_record.id}",
            json={"diagnosis": "Migraine", "treatment_notes": "Updated treatment"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["diagnosis"] == "Migraine"
        assert data["treatment_notes"] == "Updated treatment"

    @pytest.mark.asyncio
    async def test_update_record_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent medical record."""
        response = await client.put(
            "/api/v1/medical-records/99999",
            json={"diagnosis": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_record_completed_appointment_fails(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medical_record: MedicalRecord,
        appointment: Appointment,
    ):
        """Test that cannot update record of completed appointment."""
        appointment.status = "completed"
        await db_session.commit()

        response = await client.put(
            f"/api/v1/medical-records/{medical_record.id}",
            json={"diagnosis": "Updated"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()


class TestDeleteMedicalRecord:
    """Tests for DELETE /api/v1/medical-records/{id}"""

    @pytest.mark.asyncio
    async def test_delete_record_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, medical_record: MedicalRecord,
    ):
        """Test deleting medical record (soft delete)."""
        record_id = medical_record.id
        response = await client.delete(
            f"/api/v1/medical-records/{record_id}", headers=admin_headers,
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(MedicalRecord).where(MedicalRecord.id == record_id)
        )
        db_record = result.scalar_one_or_none()
        assert db_record.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_record_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent medical record."""
        response = await client.delete("/api/v1/medical-records/99999", headers=admin_headers)
        assert response.status_code == 404
