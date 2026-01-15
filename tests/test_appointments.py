import pytest
from datetime import date, time
from httpx import AsyncClient
from sqlalchemy import select
from app.models.appointment import Appointment


class TestAppointmentEndpoints:
    """Test cases for appointment endpoints."""

    async def _create_patient(self, client: AsyncClient, admin_headers: dict) -> str:
        """Helper to create a test patient."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": "Appt",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
            headers=admin_headers,
        )
        return response.json()["id"]

    async def _create_doctor(self, client: AsyncClient, admin_headers: dict) -> str:
        """Helper to create a test doctor."""
        import uuid
        response = await client.post(
            "/api/v1/doctors/",
            json={
                "first_name": "Appt",
                "last_name": "Doctor",
                "specialization": "General",
                "email": f"appt.doctor.{uuid.uuid4().hex[:8]}@example.com",
            },
            headers=admin_headers,
        )
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_appointment(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new appointment."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        appointment_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "09:30:00",
            "appointment_type": "consultation",
            "chief_complaint": "Routine checkup",
        }
        response = await client.post(
            "/api/v1/appointments/",
            json=appointment_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient_id
        assert data["doctor_id"] == doctor_id
        assert data["status"] == "scheduled"
        assert "appointment_number" in data

        # Verify in database
        result = await db_session.execute(select(Appointment).where(Appointment.id == data["id"]))
        appointment = result.scalar_one_or_none()
        assert appointment is not None

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_patient(self, client: AsyncClient, admin_headers: dict):
        """Test creating appointment with invalid patient fails."""
        doctor_id = await self._create_doctor(client, admin_headers)
        fake_patient_id = "00000000-0000-0000-0000-000000000000"

        response = await client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": fake_patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(date.today()),
                "start_time": "10:00:00",
                "end_time": "10:30:00",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Patient not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_appointments(self, client: AsyncClient, admin_headers: dict):
        """Test listing appointments."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        await client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(date.today()),
                "start_time": "11:00:00",
                "end_time": "11:30:00",
            },
            headers=admin_headers,
        )

        response = await client.get("/api/v1/appointments/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_appointments_filter_by_patient(self, client: AsyncClient, admin_headers: dict):
        """Test filtering appointments by patient."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        await client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(date.today()),
                "start_time": "14:00:00",
                "end_time": "14:30:00",
            },
            headers=admin_headers,
        )

        response = await client.get(
            f"/api/v1/appointments/?patient_id={patient_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for appt in data["data"]:
            assert appt["patient_id"] == patient_id

    @pytest.mark.asyncio
    async def test_update_appointment_status(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating appointment status."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(date.today()),
                "start_time": "15:00:00",
                "end_time": "15:30:00",
            },
            headers=admin_headers,
        )
        appointment_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/appointments/{appointment_id}",
            json={"status": "completed"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_appointment(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting an appointment."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_date": str(date.today()),
                "start_time": "16:00:00",
                "end_time": "16:30:00",
            },
            headers=admin_headers,
        )
        appointment_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/appointments/{appointment_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(Appointment).where(Appointment.id == appointment_id))
        assert result.scalar_one_or_none() is None

