import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy import select
from app.models.prescription import Prescription


class TestPrescriptionEndpoints:
    """Test cases for prescription endpoints."""

    async def _create_patient(self, client: AsyncClient, admin_headers: dict) -> str:
        """Helper to create a test patient."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": "Rx",
                "last_name": "Patient",
                "date_of_birth": "1985-05-15",
                "gender": "female",
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
                "first_name": "Rx",
                "last_name": "Doctor",
                "specialization": "Internal Medicine",
                "email": f"rx.doctor.{uuid.uuid4().hex[:8]}@example.com",
            },
            headers=admin_headers,
        )
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_prescription(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new prescription."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        prescription_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "prescription_date": str(date.today()),
            "diagnosis": "Common cold",
            "notes": "Rest and fluids",
        }
        response = await client.post(
            "/api/v1/prescriptions/",
            json=prescription_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient_id
        assert data["doctor_id"] == doctor_id
        assert data["status"] == "pending"
        assert "prescription_number" in data

        # Verify in database
        result = await db_session.execute(select(Prescription).where(Prescription.id == data["id"]))
        prescription = result.scalar_one_or_none()
        assert prescription is not None

    @pytest.mark.asyncio
    async def test_list_prescriptions(self, client: AsyncClient, admin_headers: dict):
        """Test listing prescriptions."""
        response = await client.get("/api/v1/prescriptions/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_prescriptions_filter_by_status(self, client: AsyncClient, admin_headers: dict):
        """Test filtering prescriptions by status."""
        response = await client.get(
            "/api/v1/prescriptions/?status=pending",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for rx in data["data"]:
            assert rx["status"] == "pending"

    @pytest.mark.asyncio
    async def test_update_prescription_status(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating prescription status to dispensed."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/prescriptions/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "prescription_date": str(date.today()),
            },
            headers=admin_headers,
        )
        prescription_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/prescriptions/{prescription_id}",
            json={"status": "dispensed"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "dispensed"
        assert response.json()["dispensed_at"] is not None

    @pytest.mark.asyncio
    async def test_delete_prescription(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a prescription."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/prescriptions/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "prescription_date": str(date.today()),
            },
            headers=admin_headers,
        )
        prescription_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/prescriptions/{prescription_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(Prescription).where(Prescription.id == prescription_id))
        assert result.scalar_one_or_none() is None

