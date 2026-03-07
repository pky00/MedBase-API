"""Tests for doctor endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.third_party import ThirdParty
from app.model.user import User


@pytest.fixture
async def partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a partner for doctor testing."""
    tp = ThirdParty(name="Doctor Test Partner", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    partner = Partner(
        third_party_id=tp.id,
        partner_type="both",
        organization_type="hospital",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    partner.third_party = tp
    return partner


@pytest.fixture
async def internal_doctor(db_session: AsyncSession, admin_user: User) -> Doctor:
    """Create an internal doctor for testing."""
    tp = ThirdParty(name="Dr. Internal", phone="1111111111", email="internal@clinic.com", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    doctor = Doctor(
        third_party_id=tp.id,
        specialization="General Practice",
        type="internal",
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    doctor.third_party = tp
    return doctor


@pytest.fixture
async def partner_doctor(db_session: AsyncSession, admin_user: User, partner: Partner) -> Doctor:
    """Create a partner-provided doctor for testing."""
    tp = ThirdParty(name="Dr. Partner Provided", is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    doctor = Doctor(
        third_party_id=tp.id,
        specialization="Surgery",
        type="partner_provided",
        partner_id=partner.id,
        is_active=True,
        created_by=admin_user.username,
        updated_by=admin_user.username,
    )
    db_session.add(doctor)
    await db_session.commit()
    await db_session.refresh(doctor)
    doctor.third_party = tp
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
        self, client: AsyncClient, admin_headers: dict, internal_doctor: Doctor,
    ):
        """Test filtering doctors by type."""
        response = await client.get(
            "/api/v1/doctors", params={"type": "internal"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["type"] == "internal"

    @pytest.mark.asyncio
    async def test_get_doctors_filter_by_partner_id(
        self, client: AsyncClient, admin_headers: dict,
        partner: Partner, partner_doctor: Doctor,
    ):
        """Test filtering doctors by partner_id."""
        response = await client.get(
            "/api/v1/doctors", params={"partner_id": partner.id}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["partner_id"] == partner.id

    @pytest.mark.asyncio
    async def test_get_doctors_with_search(
        self, client: AsyncClient, admin_headers: dict, internal_doctor: Doctor,
    ):
        """Test searching doctors."""
        response = await client.get(
            "/api/v1/doctors", params={"search": "Internal"}, headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestGetDoctor:
    """Tests for GET /api/v1/doctors/{id}"""

    @pytest.mark.asyncio
    async def test_get_doctor_with_details(
        self, client: AsyncClient, admin_headers: dict, internal_doctor: Doctor,
    ):
        """Test getting doctor by ID."""
        response = await client.get(
            f"/api/v1/doctors/{internal_doctor.id}", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["third_party"]["name"] == "Dr. Internal"
        assert data["type"] == "internal"
        assert data["partner_name"] is None
        assert "third_party_id" in data

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
        assert data["partner_name"] == partner.third_party.name

    @pytest.mark.asyncio
    async def test_get_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent doctor."""
        response = await client.get("/api/v1/doctors/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCreateDoctor:
    """Tests for POST /api/v1/doctors"""

    @pytest.mark.asyncio
    async def test_create_internal_doctor_auto_creates_third_party(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test creating an internal doctor auto-creates a third_party record."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. New Internal",
                "specialization": "Pediatrics",
                "phone": "222",
                "email": "new@clinic.com",
                "type": "internal",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["third_party"]["name"] == "Dr. New Internal"
        assert data["type"] == "internal"
        assert "third_party_id" in data

        # Verify third_party was created
        result = await db_session.execute(
            select(ThirdParty).where(ThirdParty.id == data["third_party_id"])
        )
        tp = result.scalar_one_or_none()
        assert tp is not None

    @pytest.mark.asyncio
    async def test_create_partner_provided_doctor(
        self, client: AsyncClient, admin_headers: dict, partner: Partner,
    ):
        """Test creating a partner-provided doctor."""
        response = await client.post(
            "/api/v1/doctors",
            json={
                "name": "Dr. From Partner",
                "type": "partner_provided",
                "partner_id": partner.id,
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
            json={"name": "Dr. No Partner", "type": "partner_provided"},
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
            json={"name": "Dr. Bad Partner", "type": "partner_provided", "partner_id": 99999},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Partner not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_duplicate_name(
        self, client: AsyncClient, admin_headers: dict, internal_doctor: Doctor,
    ):
        """Test creating doctor with duplicate name fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={"name": internal_doctor.third_party.name, "type": "internal"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_duplicate_name_in_third_parties(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession,
    ):
        """Test creating doctor with name that already exists in third_parties fails."""
        tp = ThirdParty(name="Existing TP Doctor", is_active=True)
        db_session.add(tp)
        await db_session.commit()

        response = await client.post(
            "/api/v1/doctors",
            json={"name": "Existing TP Doctor", "type": "internal"},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists in third parties" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_doctor_empty_name(self, client: AsyncClient, admin_headers: dict):
        """Test creating doctor with empty name fails."""
        response = await client.post(
            "/api/v1/doctors",
            json={"name": "", "type": "internal"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_doctor_with_existing_third_party(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession,
    ):
        """Test creating a doctor with an existing third_party_id."""
        tp = ThirdParty(name="Pre-existing TP", is_active=True)
        db_session.add(tp)
        await db_session.commit()
        await db_session.refresh(tp)

        response = await client.post(
            "/api/v1/doctors",
            json={
                "type": "external",
                "third_party_id": tp.id,
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["third_party_id"] == tp.id


class TestUpdateDoctor:
    """Tests for PUT /api/v1/doctors/{id}"""

    @pytest.mark.asyncio
    async def test_update_doctor_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, internal_doctor: Doctor,
    ):
        """Test updating a doctor."""
        response = await client.put(
            f"/api/v1/doctors/{internal_doctor.id}",
            json={"name": "Dr. Updated", "specialization": "Cardiology"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["third_party"]["name"] == "Dr. Updated"
        assert data["specialization"] == "Cardiology"

    @pytest.mark.asyncio
    async def test_update_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent doctor."""
        response = await client.put(
            "/api/v1/doctors/99999", json={"name": "Test"}, headers=admin_headers,
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
            json={"name": partner_doctor.third_party.name},
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
        doctor_id = internal_doctor.id
        response = await client.delete(
            f"/api/v1/doctors/{doctor_id}", headers=admin_headers
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        db_session.expire_all()
        result = await db_session.execute(
            select(Doctor).where(Doctor.id == doctor_id)
        )
        db_doctor = result.scalar_one_or_none()
        assert db_doctor.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_doctor_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent doctor."""
        response = await client.delete("/api/v1/doctors/99999", headers=admin_headers)
        assert response.status_code == 404
