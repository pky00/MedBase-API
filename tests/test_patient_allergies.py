import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient_allergy import PatientAllergy


@pytest.mark.asyncio
class TestPatientAllergiesCRUD:
    """Test /patients/{patient_id}/allergies CRUD endpoints."""

    async def create_test_patient(self, client: AsyncClient, admin_headers: dict) -> dict:
        """Helper to create a test patient."""
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Allergy",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )
        assert response.status_code == 201
        return response.json()

    async def test_create_patient_allergy(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test creating a new allergy for a patient."""
        patient = await self.create_test_patient(client, admin_headers)
        
        response = await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={
                "allergen": "Penicillin",
                "reaction": "Skin rash and hives",
                "severity": "severe",
                "notes": "Discovered in 2020",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["allergen"] == "Penicillin"
        assert data["severity"] == "severe"
        assert data["patient_id"] == patient["id"]

        # Verify in database
        result = await db_session.execute(
            select(PatientAllergy).where(PatientAllergy.id == uuid.UUID(data["id"]))
        )
        db_allergy = result.scalar_one()
        assert db_allergy.allergen == "Penicillin"

    async def test_create_patient_allergy_minimal(self, client: AsyncClient, admin_headers: dict):
        """Test creating an allergy with only required fields."""
        patient = await self.create_test_patient(client, admin_headers)
        
        response = await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={
                "allergen": "Peanuts",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["allergen"] == "Peanuts"
        assert data["severity"] == "moderate"  # Default value

    async def test_create_allergy_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test creating allergy for non-existent patient."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = await client.post(
            f"/api/v1/patients/{fake_uuid}/allergies/",
            headers=admin_headers,
            json={"allergen": "Peanuts"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Patient not found"

    async def test_list_patient_allergies(self, client: AsyncClient, admin_headers: dict):
        """Test listing all allergies for a patient."""
        patient = await self.create_test_patient(client, admin_headers)
        
        # Create multiple allergies
        await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={"allergen": "Penicillin", "severity": "severe"},
        )
        await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={"allergen": "Peanuts", "severity": "mild"},
        )

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["data"]) == 2

    async def test_get_patient_allergy_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting a specific allergy by ID."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={"allergen": "Latex"},
        )
        allergy_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/allergies/{allergy_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == allergy_id
        assert data["allergen"] == "Latex"

    async def test_get_allergy_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent allergy."""
        patient = await self.create_test_patient(client, admin_headers)
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/patients/{patient['id']}/allergies/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_update_patient_allergy(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test updating an allergy."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={"allergen": "Shellfish", "severity": "mild"},
        )
        allergy_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/patients/{patient['id']}/allergies/{allergy_id}",
            headers=admin_headers,
            json={"severity": "life_threatening", "reaction": "Anaphylaxis"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "life_threatening"
        assert data["reaction"] == "Anaphylaxis"

        # Verify in database
        result = await db_session.execute(
            select(PatientAllergy).where(PatientAllergy.id == uuid.UUID(allergy_id))
        )
        db_allergy = result.scalar_one()
        assert db_allergy.severity.value == "life_threatening"

    async def test_delete_patient_allergy(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test deleting an allergy."""
        patient = await self.create_test_patient(client, admin_headers)
        
        create_response = await client.post(
            f"/api/v1/patients/{patient['id']}/allergies/",
            headers=admin_headers,
            json={"allergen": "Dust mites"},
        )
        allergy_id = create_response.json()["id"]

        # Verify exists
        result = await db_session.execute(
            select(PatientAllergy).where(PatientAllergy.id == uuid.UUID(allergy_id))
        )
        assert result.scalar_one_or_none() is not None

        response = await client.delete(
            f"/api/v1/patients/{patient['id']}/allergies/{allergy_id}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify deleted
        result = await db_session.execute(
            select(PatientAllergy).where(PatientAllergy.id == uuid.UUID(allergy_id))
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_allergy_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent allergy."""
        patient = await self.create_test_patient(client, admin_headers)
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(
            f"/api/v1/patients/{patient['id']}/allergies/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to allergy endpoints."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/patients/{fake_uuid}/allergies/")
        assert response.status_code == 401

