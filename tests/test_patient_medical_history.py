import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient_medical_history import PatientMedicalHistory


@pytest.mark.asyncio
class TestPatientMedicalHistoryCRUD:
    """Test /patients/{patient_id}/medical-history CRUD endpoints."""

    async def create_test_patient(self, client: AsyncClient, admin_headers: dict) -> dict:
        """Helper to create a test patient."""
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "History",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "gender": "female",
            },
        )
        assert response.status_code == 201
        return response.json()

    async def test_create_medical_history(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test creating a new medical history entry."""
        patient = await self.create_test_patient(client, admin_headers)
        
        response = await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={
                "condition_name": "Type 2 Diabetes",
                "icd_code": "E11",
                "diagnosis_date": "2020-03-15",
                "is_chronic": True,
                "is_current": True,
                "severity": "moderate",
                "notes": "Managed with metformin",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["condition_name"] == "Type 2 Diabetes"
        assert data["icd_code"] == "E11"
        assert data["is_chronic"] is True
        assert data["patient_id"] == patient["id"]

        # Verify in database
        result = await db_session.execute(
            select(PatientMedicalHistory).where(PatientMedicalHistory.id == uuid.UUID(data["id"]))
        )
        db_history = result.scalar_one()
        assert db_history.condition_name == "Type 2 Diabetes"

    async def test_create_medical_history_minimal(self, client: AsyncClient, admin_headers: dict):
        """Test creating medical history with only required fields."""
        patient = await self.create_test_patient(client, admin_headers)
        
        response = await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={
                "condition_name": "Appendectomy",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["condition_name"] == "Appendectomy"
        assert data["is_chronic"] is False
        assert data["is_current"] is True

    async def test_create_history_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test creating history for non-existent patient."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = await client.post(
            f"/api/v1/patients/{fake_uuid}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Hypertension"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Patient not found"

    async def test_list_medical_history(self, client: AsyncClient, admin_headers: dict):
        """Test listing all medical history for a patient."""
        patient = await self.create_test_patient(client, admin_headers)
        
        # Create multiple entries
        await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Hypertension", "is_current": True},
        )
        await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Appendectomy", "is_current": False},
        )

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["data"]) == 2

    async def test_list_medical_history_current_only(self, client: AsyncClient, admin_headers: dict):
        """Test listing only current medical conditions."""
        patient = await self.create_test_patient(client, admin_headers)
        
        # Create entries
        await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Hypertension", "is_current": True},
        )
        await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Appendectomy", "is_current": False},
        )

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            params={"current_only": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["condition_name"] == "Hypertension"

    async def test_get_medical_history_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting a specific history entry by ID."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Asthma"},
        )
        history_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/medical-history/{history_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == history_id
        assert data["condition_name"] == "Asthma"

    async def test_get_history_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent history entry."""
        patient = await self.create_test_patient(client, admin_headers)
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/medical-history/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_update_medical_history(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test updating a medical history entry."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Flu", "is_current": True},
        )
        history_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/patients/{patient['id']}/medical-history/{history_id}",
            headers=admin_headers,
            json={"is_current": False, "resolution_date": "2024-01-15"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_current"] is False
        assert data["resolution_date"] == "2024-01-15"

        # Verify in database
        result = await db_session.execute(
            select(PatientMedicalHistory).where(PatientMedicalHistory.id == uuid.UUID(history_id))
        )
        db_history = result.scalar_one()
        assert db_history.is_current is False

    async def test_delete_medical_history(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test deleting a medical history entry."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/medical-history/",
            headers=admin_headers,
            json={"condition_name": "Old condition"},
        )
        history_id = create_response.json()["id"]

        # Verify exists
        result = await db_session.execute(
            select(PatientMedicalHistory).where(PatientMedicalHistory.id == uuid.UUID(history_id))
        )
        assert result.scalar_one_or_none() is not None

        response = await client.delete(
            f"/api/v1/patients/{patient['id']}/medical-history/{history_id}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(
            select(PatientMedicalHistory).where(PatientMedicalHistory.id == uuid.UUID(history_id))
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_history_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent history entry."""
        patient = await self.create_test_patient(client, admin_headers)
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(
            f"/api/v1/patients/{patient['id']}/medical-history/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to medical history endpoints."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/patients/{fake_uuid}/medical-history/")
        assert response.status_code == 401

