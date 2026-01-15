import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.doctor import Doctor


@pytest.mark.asyncio
class TestDoctorsCRUD:
    """Test /doctors CRUD endpoints."""

    async def test_create_doctor(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test creating a new doctor."""
        unique_id = uuid.uuid4().hex[:8]
        
        response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "John",
                "last_name": "Smith",
                "specialization": "Cardiology",
                "gender": "male",
                "phone": "+1234567890",
                "email": f"dr.smith_{unique_id}@medbase.example",
                "qualification": "MD, FACC",
                "bio": "Experienced cardiologist",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Smith"
        assert data["specialization"] == "Cardiology"
        assert data["gender"] == "male"
        assert "id" in data

        # Verify doctor exists in database
        result = await db_session.execute(select(Doctor).where(Doctor.id == uuid.UUID(data["id"])))
        db_doctor = result.scalar_one()
        assert db_doctor.first_name == "John"
        assert db_doctor.specialization == "Cardiology"

    async def test_create_doctor_minimal(self, client: AsyncClient, admin_headers: dict):
        """Test creating a doctor with only required fields."""
        response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "specialization": "General Practice",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["gender"] is None
        assert data["email"] is None

    async def test_create_doctor_duplicate_email(self, client: AsyncClient, admin_headers: dict):
        """Test creating doctor with existing email fails."""
        unique_id = uuid.uuid4().hex[:8]
        email = f"duplicate_{unique_id}@medbase.example"
        
        # Create first doctor
        await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "First",
                "last_name": "Doctor",
                "specialization": "Surgery",
                "email": email,
            },
        )

        # Try to create second doctor with same email
        response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Second",
                "last_name": "Doctor",
                "specialization": "Pediatrics",
                "email": email,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    async def test_create_doctor_with_user_id(self, client: AsyncClient, admin_headers: dict, test_user: dict):
        """Test creating a doctor linked to a user account."""
        response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Linked",
                "last_name": "Doctor",
                "specialization": "Neurology",
                "user_id": test_user["id"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user["id"]

    async def test_create_doctor_invalid_user_id(self, client: AsyncClient, admin_headers: dict):
        """Test creating doctor with non-existent user_id fails."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Invalid",
                "last_name": "Doctor",
                "specialization": "Dermatology",
                "user_id": fake_uuid,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "User not found"

    async def test_create_doctor_unauthorized(self, client: AsyncClient):
        """Test creating doctor without auth fails."""
        response = await client.post(
            "/api/v1/doctors/",
            json={
                "first_name": "Unauthorized",
                "last_name": "Doctor",
                "specialization": "Orthopedics",
            },
        )

        assert response.status_code == 401

    async def test_list_doctors(self, client: AsyncClient, admin_headers: dict):
        """Test listing doctors with pagination."""
        # Create a doctor first
        await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "List",
                "last_name": "Test",
                "specialization": "Oncology",
            },
        )

        response = await client.get("/api/v1/doctors/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["data"]) >= 1

    async def test_list_doctors_pagination(self, client: AsyncClient, admin_headers: dict):
        """Test listing doctors with custom pagination."""
        response = await client.get(
            "/api/v1/doctors/",
            headers=admin_headers,
            params={"page": 1, "size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    async def test_list_doctors_filter_by_specialization(self, client: AsyncClient, admin_headers: dict):
        """Test filtering doctors by specialization."""
        unique_id = uuid.uuid4().hex[:8]
        specialization = f"Unique_Specialty_{unique_id}"
        
        # Create a doctor with unique specialization
        await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Specialist",
                "last_name": "Doctor",
                "specialization": specialization,
            },
        )

        response = await client.get(
            "/api/v1/doctors/",
            headers=admin_headers,
            params={"specialization": specialization},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(specialization.lower() in d["specialization"].lower() for d in data["data"])

    async def test_get_doctor_by_id(self, client: AsyncClient, admin_headers: dict):
        """Test getting doctor by ID."""
        # Create a doctor
        create_response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Get",
                "last_name": "ById",
                "specialization": "Psychiatry",
            },
        )
        doctor_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/doctors/{doctor_id}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doctor_id
        assert data["first_name"] == "Get"

    async def test_get_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting nonexistent doctor returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/doctors/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Doctor not found"

    async def test_update_doctor(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test updating doctor by ID."""
        # Create a doctor
        create_response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": "Update",
                "last_name": "Test",
                "specialization": "Radiology",
            },
        )
        doctor_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/doctors/{doctor_id}",
            headers=admin_headers,
            json={"specialization": "Interventional Radiology", "phone": "+9876543210"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["specialization"] == "Interventional Radiology"
        assert data["phone"] == "+9876543210"

        # Verify in database
        result = await db_session.execute(select(Doctor).where(Doctor.id == uuid.UUID(doctor_id)))
        db_doctor = result.scalar_one()
        assert db_doctor.specialization == "Interventional Radiology"

    async def test_update_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating nonexistent doctor returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.patch(
            f"/api/v1/doctors/{fake_uuid}",
            headers=admin_headers,
            json={"specialization": "New Specialty"},
        )

        assert response.status_code == 404

    async def test_delete_doctor(self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
        """Test deleting a doctor."""
        unique_id = uuid.uuid4().hex[:8]
        
        # Create a doctor to delete
        create_response = await client.post(
            "/api/v1/doctors/",
            headers=admin_headers,
            json={
                "first_name": f"Delete_{unique_id}",
                "last_name": "Me",
                "specialization": "Anesthesiology",
            },
        )
        assert create_response.status_code == 201
        doctor_id = create_response.json()["id"]

        # Verify doctor exists
        result = await db_session.execute(select(Doctor).where(Doctor.id == uuid.UUID(doctor_id)))
        assert result.scalar_one_or_none() is not None

        response = await client.delete(
            f"/api/v1/doctors/{doctor_id}",
            headers=admin_headers,
        )

        assert response.status_code == 204

        # Verify doctor was removed from database
        result = await db_session.execute(select(Doctor).where(Doctor.id == uuid.UUID(doctor_id)))
        assert result.scalar_one_or_none() is None

    async def test_delete_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting nonexistent doctor returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/doctors/{fake_uuid}",
            headers=admin_headers,
        )

        assert response.status_code == 404

