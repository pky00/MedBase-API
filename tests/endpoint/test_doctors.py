"""Tests for doctor endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.user import User


@pytest.fixture
async def partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a partner for doctor testing."""
    partner = Partner(
        name="Doctor Test Partner",
        partner_type="both",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def internal_doctor(db_session: AsyncSession, admin_user: User) -> Doctor:
    """Create an internal doctor for testing."""
    doctor = Doctor(
        name="Dr. Internal",
        specialization="General Practice",
        phone="1111111111",
        email="internal@clinic.com",
        type="internal",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


@pytest.fixture
async def partner_doctor(db_session: AsyncSession, admin_user: User, partner: Partner) -> Doctor:
    """Create a partner-provided doctor for testing."""
    doctor = Doctor(
        name="Dr. Partner Provided",
        specialization="Surgery",
        type="partner_provided",
        partner_id=partner.id,
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    return doctor


class TestGetDoctors:
    """Tests for GET /api/v1/doctors"""

    @pytest.mark.asyncio
    async def test_get_doctors_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting doctors list."""
        response = await client.get("/api/v1/doctors", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_doctors_unauthenticated(self, client: AsyncClient):
        """Test getting doctors without authentication."""
        response = await client.get("/api/v1/doctors")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_doctors_filter_by_type(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor,
    ):
        """Test filtering doctors by type."""
        response = await client.get(
            "/api/v1/doctors",
            params={"type": "internal"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["type"] == "internal"

    @pytest.mark.asyncio
    async def test_get_doctors_filter_by_is_active(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test filtering doctors by active status."""
        d1 = Doctor(
            name="Active Doctor", type="internal", is_active=True,
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        d2 = Doctor(
            name="Inactive Doctor", type="internal", is_active=False,
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        db_session.add_all([d1, d2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/doctors",
            params={"is_active": True},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_doctors_filter_by_partner_id(
        self, client: AsyncClient, admin_headers: dict,
        partner: Partner, partner_doctor: Doctor,
    ):
        """Test filtering doctors by partner_id."""
        response = await client.get(
            "/api/v1/doctors",
            params={"partner_id": partner.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["partner_id"] == partner.id

    @pytest.mark.asyncio
    async def test_get_doctors_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test searching doctors by name/specialization."""
        d1 = Doctor(
            name="Dr. Cardiology", specialization="Cardiology", type="internal",
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        d2 = Doctor(
            name="Dr. Neurology", specialization="Neurology", type="internal",
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        db_session.add_all([d1, d2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/doctors",
            params={"search": "Cardiology"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # Should match either by name or specialization
        found = any("Cardiology" in item["name"] or item.get("specialization") == "Cardiology" for item in data["items"])
        assert found

    @pytest.mark.asyncio
    async def test_get_doctors_pagination(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test pagination of doctors."""
        for i in range(5):
            d = Doctor(
                name=f"Dr. Paginate {i}", type="internal",
                created_by=admin_user.id, updated_by=admin_user.id,
            )
            db_session.add(d)
        await db_session.commit()

        response = await client.get(
            "/api/v1/doctors",
            params={"page": 1, "size": 2},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


class TestGetDoctor:
    """Tests for GET /api/v1/doctors/{id}"""

    @pytest.mark.asyncio
    async def test_get_doctor_with_details(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor,
    ):
        """Test getting doctor by ID."""
        response = await client.get(
            f"/api/v1/doctors/{internal_doctor.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Internal"
        assert data["type"] == "internal"
        assert data["partner_name"] is None

    @pytest.mark.asyncio
    async def test_get_partner_provided_doctor_with_partner_name(
        self, client: AsyncClient, admin_headers: dict,
        partner_doctor: Doctor, partner: Partner,
    ):
        """Test getting partner-provided doctor includes partner name."""
        response = await client.get(
            f"/api/v1/doctors/{partner_doctor.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Partner Provided"
        assert data["partner_name"] == partner.name

    @pytest.mark.asyncio
    async def test_get_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent doctor."""
        response = await client.get(
            "/api/v1/doctors/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreateDoctor:
    """Tests for POST /api/v1/doctors"""

    @pytest.mark.asyncio
    async def test_create_internal_doctor(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test creating an internal doctor and verify in database."""
        doctor_data = {
            "name": "Dr. New Internal",
            "specialization": "Pediatrics",
            "phone": "2222222222",
            "email": "new@clinic.com",
            "type": "internal",
            "is_active": True,
        }

        response = await client.post(
            "/api/v1/doctors",
            json=doctor_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dr. New Internal"
        assert data["type"] == "internal"
        assert data["specialization"] == "Pediatrics"

        # Verify in database
        result = await db_session.execute(
            select(Doctor).where(Doctor.id == data["id"])
        )
        db_doctor = result.scalar_one_or_none()
        assert db_doctor is not None
        assert db_doctor.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_external_doctor(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating an external doctor."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. External",
                "type": "external",
                "specialization": "Orthopedics",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "external"

    @pytest.mark.asyncio
    async def test_create_partner_provided_doctor(
        self, client: AsyncClient, admin_headers: dict,
        partner: Partner,
    ):
        """Test creating a partner-provided doctor with partner_id."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. From Partner",
                "type": "partner_provided",
                "partner_id": partner.id,
                "specialization": "Dermatology",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "partner_provided"
        assert data["partner_id"] == partner.id

    @pytest.mark.asyncio
    async def test_create_partner_provided_without_partner_id(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating partner_provided doctor without partner_id fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. No Partner",
                "type": "partner_provided",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Partner ID is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_invalid_partner(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating doctor with non-existent partner fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. Bad Partner",
                "type": "partner_provided",
                "partner_id": 99999,
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Partner not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_duplicate_name(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor,
    ):
        """Test creating doctor with duplicate name fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": internal_doctor.name,
                "type": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_empty_name(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating doctor with empty name fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={"name": "", "type": "internal"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_doctor_invalid_type(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating doctor with invalid type fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={"name": "Dr. Bad Type", "type": "invalid"},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateDoctor:
    """Tests for PUT /api/v1/doctors/{id}"""

    @pytest.mark.asyncio
    async def test_update_doctor_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, internal_doctor: Doctor,
    ):
        """Test updating a doctor and verify in database."""
        response = await client.put(
            f"/api/v1/doctors/{internal_doctor.id}",
            json={"name": "Dr. Updated", "specialization": "Cardiology"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Updated"
        assert data["specialization"] == "Cardiology"

        # Verify in database
        db_session.expire_all()
        result = await db_session.execute(
            select(Doctor).where(Doctor.id == internal_doctor.id)
        )
        db_doctor = result.scalar_one_or_none()
        assert db_doctor.name == "Dr. Updated"
        assert db_doctor.updated_by == admin_user.id

    @pytest.mark.asyncio
    async def test_update_doctor_change_to_partner_provided(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor, partner: Partner,
    ):
        """Test changing doctor type to partner_provided with partner_id."""
        response = await client.put(
            f"/api/v1/doctors/{internal_doctor.id}",
            json={"type": "partner_provided", "partner_id": partner.id},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "partner_provided"
        assert data["partner_id"] == partner.id

    @pytest.mark.asyncio
    async def test_update_doctor_partner_provided_without_partner_id(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor,
    ):
        """Test changing to partner_provided without partner_id fails."""
        response = await client.put(
            f"/api/v1/doctors/{internal_doctor.id}",
            json={"type": "partner_provided"},
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Partner ID is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent doctor."""
        response = await client.put(
            "/api/v1/doctors/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_doctor_duplicate_name(
        self, client: AsyncClient, admin_headers: dict,
        internal_doctor: Doctor, partner_doctor: Doctor,
    ):
        """Test updating doctor with duplicate name fails."""
        response = await client.put(
            f"/api/v1/doctors/{internal_doctor.id}",
            json={"name": partner_doctor.name},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestDeleteDoctor:
    """Tests for DELETE /api/v1/doctors/{id}"""

    @pytest.mark.asyncio
    async def test_delete_doctor_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, internal_doctor: Doctor,
    ):
        """Test deleting doctor (soft delete)."""
        response = await client.delete(
            f"/api/v1/doctors/{internal_doctor.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(Doctor).where(Doctor.id == internal_doctor.id)
        )
        db_doctor = result.scalar_one_or_none()
        assert db_doctor is not None
        assert db_doctor.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent doctor."""
        response = await client.delete(
            "/api/v1/doctors/99999", headers=admin_headers
        )
        assert response.status_code == 404
