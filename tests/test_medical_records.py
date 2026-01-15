import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy import select
from app.models.medical_record import MedicalRecord


class TestMedicalRecordEndpoints:
    """Test cases for medical record endpoints."""

    async def _create_patient(self, client: AsyncClient, admin_headers: dict) -> str:
        """Helper to create a test patient."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": "Record",
                "last_name": "Patient",
                "date_of_birth": "1980-03-20",
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
                "first_name": "Record",
                "last_name": "Doctor",
                "specialization": "Family Medicine",
                "email": f"record.doctor.{uuid.uuid4().hex[:8]}@example.com",
            },
            headers=admin_headers,
        )
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_medical_record(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test creating a new medical record."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        record_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "visit_date": str(date.today()),
            "chief_complaint": "Headache and fever",
            "diagnosis": ["Viral infection", "Tension headache"],
            "treatment_plan": "Rest, fluids, acetaminophen",
        }
        response = await client.post(
            "/api/v1/medical-records/",
            json=record_data,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == patient_id
        assert "record_number" in data

        # Verify in database
        result = await db_session.execute(select(MedicalRecord).where(MedicalRecord.id == data["id"]))
        record = result.scalar_one_or_none()
        assert record is not None

    @pytest.mark.asyncio
    async def test_list_medical_records(self, client: AsyncClient, admin_headers: dict):
        """Test listing medical records."""
        response = await client.get("/api/v1/medical-records/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_medical_records_filter_by_patient(self, client: AsyncClient, admin_headers: dict):
        """Test filtering medical records by patient."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        await client.post(
            "/api/v1/medical-records/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "visit_date": str(date.today()),
            },
            headers=admin_headers,
        )

        response = await client.get(
            f"/api/v1/medical-records/?patient_id={patient_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for record in data["data"]:
            assert record["patient_id"] == patient_id

    @pytest.mark.asyncio
    async def test_update_medical_record(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test updating a medical record."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/medical-records/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "visit_date": str(date.today()),
            },
            headers=admin_headers,
        )
        record_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/medical-records/{record_id}",
            json={
                "assessment": "Patient improving",
                "follow_up_instructions": "Return in 1 week if symptoms persist",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["assessment"] == "Patient improving"

    @pytest.mark.asyncio
    async def test_delete_medical_record(self, client: AsyncClient, admin_headers: dict, db_session):
        """Test deleting a medical record."""
        patient_id = await self._create_patient(client, admin_headers)
        doctor_id = await self._create_doctor(client, admin_headers)

        create_response = await client.post(
            "/api/v1/medical-records/",
            json={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "visit_date": str(date.today()),
            },
            headers=admin_headers,
        )
        record_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/medical-records/{record_id}", headers=admin_headers)
        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(select(MedicalRecord).where(MedicalRecord.id == record_id))
        assert result.scalar_one_or_none() is None

