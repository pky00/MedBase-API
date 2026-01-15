import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.patient import Patient


@pytest.mark.asyncio
class TestPatientsCRUD:
    """Test /patients CRUD endpoints."""

    async def test_create_patient(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test creating a new patient."""
        unique_id = uuid.uuid4().hex[:8]
        
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-05-15",
                "gender": "male",
                "blood_type": "A+",
                "phone": "+1234567890",
                "email": f"john.doe_{unique_id}@medbase.example",
                "national_id": f"NID{unique_id}",
                "city": "New York",
                "country": "USA",
                "marital_status": "single",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["gender"] == "male"
        assert data["blood_type"] == "A+"
        assert data["patient_number"].startswith("P")
        assert "id" in data

        # Verify patient exists in database
        result = await db_session.execute(select(Patient).where(Patient.id == uuid.UUID(data["id"])))
        db_patient = result.scalar_one()
        assert db_patient.first_name == "John"
        assert db_patient.patient_number == data["patient_number"]

    async def test_create_patient_minimal(self, client: AsyncClient, admin_headers: dict):
        """Test creating a patient with only required fields."""
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1985-03-20",
                "gender": "female",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["blood_type"] == "unknown"
        assert data["country"] == "Unknown"
        assert data["email"] is None

    async def test_create_patient_duplicate_email(self, client: AsyncClient, admin_headers: dict):
        """Test creating patient with existing email fails."""
        unique_id = uuid.uuid4().hex[:8]
        email = f"duplicate_{unique_id}@medbase.example"
        
        # Create first patient
        await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "First",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "email": email,
            },
        )

        # Try to create second patient with same email
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Second",
                "last_name": "Patient",
                "date_of_birth": "1992-02-02",
                "gender": "female",
                "email": email,
            },
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    async def test_create_patient_duplicate_national_id(self, client: AsyncClient, admin_headers: dict):
        """Test creating patient with existing national ID fails."""
        unique_id = uuid.uuid4().hex[:8]
        national_id = f"NID{unique_id}"
        
        # Create first patient
        await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "First",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "national_id": national_id,
            },
        )

        # Try to create second patient with same national ID
        response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Second",
                "last_name": "Patient",
                "date_of_birth": "1992-02-02",
                "gender": "female",
                "national_id": national_id,
            },
        )

        assert response.status_code == 400
        assert "national id" in response.json()["detail"].lower()

    async def test_create_patient_unauthorized(self, client: AsyncClient):
        """Test creating patient without auth fails."""
        response = await client.post(
            "/api/v1/patients/",
            json={
                "first_name": "Unauthorized",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )

        assert response.status_code == 401

    async def test_list_patients(self, client: AsyncClient, admin_headers: dict):
        """Test listing patients with pagination."""
        # Create a patient first
        await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "List",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )

        response = await client.get("/api/v1/patients/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["data"]) >= 1

    async def test_list_patients_pagination(self, client: AsyncClient, admin_headers: dict):
        """Test listing patients with custom pagination."""
        response = await client.get(
            "/api/v1/patients/",
            headers=admin_headers,
            params={"page": 1, "size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_list_patients_search(self, client: AsyncClient, admin_headers: dict):
        """Test searching patients by name."""
        unique_id = uuid.uuid4().hex[:8]
        first_name = f"Searchable_{unique_id}"
        
        # Create a patient with unique name
        await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": first_name,
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )

        response = await client.get(
            "/api/v1/patients/",
            headers=admin_headers,
            params={"search": first_name},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(first_name in p["first_name"] for p in data["data"])

    async def test_get_patient_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting patient by ID."""
        # Create a patient
        create_response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Get",
                "last_name": "ById",
                "date_of_birth": "1990-01-01",
                "gender": "female",
            },
        )
        patient_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["first_name"] == "Get"

    async def test_get_patient_by_number(self, client: AsyncClient, admin_headers: dict):
        """Test getting patient by patient number."""
        # Create a patient
        create_response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Get",
                "last_name": "ByNumber",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )
        patient_number = create_response.json()["patient_number"]

        response = await client.get(
            f"/api/v1/patients/number/{patient_number}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["patient_number"] == patient_number
        assert data["first_name"] == "Get"

    async def test_get_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting nonexistent patient returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/patients/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Patient not found"

    async def test_update_patient(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test updating patient by ID."""
        # Create a patient
        create_response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Update",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )
        patient_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
            json={"city": "Los Angeles", "phone": "+9876543210"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Los Angeles"
        assert data["phone"] == "+9876543210"

        # Verify in database
        result = await db_session.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
        db_patient = result.scalar_one()
        assert db_patient.city == "Los Angeles"

    async def test_update_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating nonexistent patient returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.patch(
            f"/api/v1/patients/{fake_uuid}",
            headers=admin_headers,
            json={"city": "New City"},
        )

        assert response.status_code == 404

    async def test_delete_patient(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test deleting a patient."""
        unique_id = uuid.uuid4().hex[:8]
        
        # Create a patient to delete
        create_response = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": f"Delete_{unique_id}",
                "last_name": "Me",
                "date_of_birth": "1990-01-01",
                "gender": "female",
            },
        )
        assert create_response.status_code == 201
        patient_id = create_response.json()["id"]

        # Verify patient exists
        result = await db_session.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
        assert result.scalar_one_or_none() is not None

        response = await client.delete(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify patient was removed from database
        result = await db_session.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
        assert result.scalar_one_or_none() is None

    async def test_delete_patient_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting nonexistent patient returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/patients/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

    async def test_patient_number_auto_increment(self, client: AsyncClient, admin_headers: dict):
        """Test that patient numbers are auto-incremented."""
        # Create two patients
        response1 = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "First",
                "last_name": "AutoNum",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )
        
        response2 = await client.post(
            "/api/v1/patients/",
            headers=admin_headers,
            json={
                "first_name": "Second",
                "last_name": "AutoNum",
                "date_of_birth": "1991-02-02",
                "gender": "female",
            },
        )

        num1 = response1.json()["patient_number"]
        num2 = response2.json()["patient_number"]
        
        # Both should start with 'P' and second should be greater
        assert num1.startswith("P")
        assert num2.startswith("P")
        assert int(num2[1:]) > int(num1[1:])

