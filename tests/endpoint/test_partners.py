"""Tests for partner endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.partner import Partner
from app.model.user import User


@pytest.fixture
async def donor_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a donor partner for testing."""
    partner = Partner(
        name="Test Donor NGO",
        partner_type="donor",
        organization_type="NGO",
        contact_person="John Doe",
        phone="1234567890",
        email="donor@test.com",
        address="123 Donor St",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


@pytest.fixture
async def referral_partner(db_session: AsyncSession, admin_user: User) -> Partner:
    """Create a referral partner for testing."""
    partner = Partner(
        name="Test Referral Hospital",
        partner_type="referral",
        organization_type="hospital",
        contact_person="Jane Smith",
        phone="9876543210",
        email="referral@test.com",
        address="456 Hospital Ave",
        is_active=True,
        created_by=admin_user.id,
        updated_by=admin_user.id,
    )
    db_session.add(partner)
    await db_session.commit()
    await db_session.refresh(partner)
    return partner


class TestGetPartners:
    """Tests for GET /api/v1/partners"""

    @pytest.mark.asyncio
    async def test_get_partners_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting partners list."""
        response = await client.get("/api/v1/partners", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_partners_unauthenticated(self, client: AsyncClient):
        """Test getting partners without authentication."""
        response = await client.get("/api/v1/partners")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_partners_with_partner_type_filter(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner, referral_partner: Partner,
    ):
        """Test filtering partners by partner_type."""
        response = await client.get(
            "/api/v1/partners",
            params={"partner_type": "donor"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["partner_type"] == "donor"

    @pytest.mark.asyncio
    async def test_get_partners_with_organization_type_filter(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner,
    ):
        """Test filtering partners by organization_type."""
        response = await client.get(
            "/api/v1/partners",
            params={"organization_type": "NGO"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["organization_type"] == "NGO"

    @pytest.mark.asyncio
    async def test_get_partners_with_is_active_filter(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test filtering by active status."""
        p1 = Partner(
            name="Active Partner", partner_type="donor", is_active=True,
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        p2 = Partner(
            name="Inactive Partner", partner_type="donor", is_active=False,
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        db_session.add_all([p1, p2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/partners",
            params={"is_active": True},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_partners_with_search(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test searching partners."""
        p1 = Partner(
            name="Alpha NGO", partner_type="donor", contact_person="Alice",
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        p2 = Partner(
            name="Beta Hospital", partner_type="referral", contact_person="Bob",
            created_by=admin_user.id, updated_by=admin_user.id,
        )
        db_session.add_all([p1, p2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/partners",
            params={"search": "Alpha"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Alpha NGO"

    @pytest.mark.asyncio
    async def test_get_partners_pagination(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test pagination of partners."""
        for i in range(5):
            p = Partner(
                name=f"Partner {i}", partner_type="donor",
                created_by=admin_user.id, updated_by=admin_user.id,
            )
            db_session.add(p)
        await db_session.commit()

        response = await client.get(
            "/api/v1/partners",
            params={"page": 1, "size": 2},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5


class TestGetPartner:
    """Tests for GET /api/v1/partners/{id}"""

    @pytest.mark.asyncio
    async def test_get_partner_with_details(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner,
    ):
        """Test getting partner by ID with details."""
        response = await client.get(
            f"/api/v1/partners/{donor_partner.id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Donor NGO"
        assert data["partner_type"] == "donor"
        assert "donations" in data

    @pytest.mark.asyncio
    async def test_get_partner_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent partner."""
        response = await client.get(
            "/api/v1/partners/99999", headers=admin_headers
        )
        assert response.status_code == 404


class TestCreatePartner:
    """Tests for POST /api/v1/partners"""

    @pytest.mark.asyncio
    async def test_create_partner_donor(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test creating a donor partner and verify in database."""
        partner_data = {
            "name": "New Donor",
            "partner_type": "donor",
            "organization_type": "NGO",
            "contact_person": "Test Person",
            "phone": "1111111111",
            "email": "new@donor.com",
            "address": "123 New St",
            "is_active": True,
        }

        response = await client.post(
            "/api/v1/partners",
            json=partner_data,
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Donor"
        assert data["partner_type"] == "donor"
        assert data["organization_type"] == "NGO"

        # Verify in database
        result = await db_session.execute(
            select(Partner).where(Partner.id == data["id"])
        )
        db_partner = result.scalar_one_or_none()
        assert db_partner is not None
        assert db_partner.name == "New Donor"
        assert db_partner.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_partner_referral(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating a referral partner."""
        response = await client.post(
            "/api/v1/partners",
            json={
                "name": "New Hospital",
                "partner_type": "referral",
                "organization_type": "hospital",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_type"] == "referral"
        assert data["organization_type"] == "hospital"

    @pytest.mark.asyncio
    async def test_create_partner_both(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating a partner with type 'both'."""
        response = await client.post(
            "/api/v1/partners",
            json={
                "name": "Dual Purpose Partner",
                "partner_type": "both",
                "organization_type": "medical_center",
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["partner_type"] == "both"

    @pytest.mark.asyncio
    async def test_create_partner_duplicate_name(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner,
    ):
        """Test creating partner with duplicate name fails."""
        response = await client.post(
            "/api/v1/partners",
            json={
                "name": donor_partner.name,
                "partner_type": "donor",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_partner_invalid_type(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating partner with invalid partner_type."""
        response = await client.post(
            "/api/v1/partners",
            json={
                "name": "Bad Partner",
                "partner_type": "invalid_type",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_partner_empty_name(
        self, client: AsyncClient, admin_headers: dict,
    ):
        """Test creating partner with empty name fails."""
        response = await client.post(
            "/api/v1/partners",
            json={"name": "", "partner_type": "donor"},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdatePartner:
    """Tests for PUT /api/v1/partners/{id}"""

    @pytest.mark.asyncio
    async def test_update_partner_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession, donor_partner: Partner,
    ):
        """Test updating a partner and verify in database."""
        response = await client.put(
            f"/api/v1/partners/{donor_partner.id}",
            json={"name": "Updated Donor Name", "contact_person": "New Contact"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Donor Name"
        assert data["contact_person"] == "New Contact"

        # Verify in database
        db_session.expire_all()
        result = await db_session.execute(
            select(Partner).where(Partner.id == donor_partner.id)
        )
        db_partner = result.scalar_one_or_none()
        assert db_partner.name == "Updated Donor Name"
        assert db_partner.updated_by == admin_user.id

    @pytest.mark.asyncio
    async def test_update_partner_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent partner."""
        response = await client.put(
            "/api/v1/partners/99999",
            json={"name": "Test"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_partner_duplicate_name(
        self, client: AsyncClient, admin_headers: dict,
        donor_partner: Partner, referral_partner: Partner,
    ):
        """Test updating partner with duplicate name fails."""
        response = await client.put(
            f"/api/v1/partners/{donor_partner.id}",
            json={"name": referral_partner.name},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestDeletePartner:
    """Tests for DELETE /api/v1/partners/{id}"""

    @pytest.mark.asyncio
    async def test_delete_partner_success(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, donor_partner: Partner,
    ):
        """Test deleting partner (soft delete)."""
        response = await client.delete(
            f"/api/v1/partners/{donor_partner.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(Partner).where(Partner.id == donor_partner.id)
        )
        db_partner = result.scalar_one_or_none()
        assert db_partner is not None
        assert db_partner.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_partner_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent partner."""
        response = await client.delete(
            "/api/v1/partners/99999", headers=admin_headers
        )
        assert response.status_code == 404
