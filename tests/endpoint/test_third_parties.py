"""Tests for third party endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.third_party import ThirdParty
from app.model.user import User
from app.model.doctor import Doctor
from app.model.patient import Patient
from app.model.partner import Partner


class TestGetThirdParties:
    """Tests for GET /api/v1/third-parties"""

    @pytest.mark.asyncio
    async def test_get_third_parties_authenticated(
        self, client: AsyncClient, admin_user: User, admin_headers: dict
    ):
        """Test getting third parties list. Admin user creates a third_party automatically."""
        response = await client.get("/api/v1/third-parties", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        # At least 1 third party (the admin user's)
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_third_parties_unauthenticated(self, client: AsyncClient):
        """Test getting third parties without authentication."""
        response = await client.get("/api/v1/third-parties")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_third_parties_filter_by_is_active(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test filtering by active status."""
        # Create an inactive third party
        tp = ThirdParty(name="Inactive TP", is_active=False)
        db_session.add(tp)
        await db_session.commit()

        response = await client.get(
            "/api/v1/third-parties",
            params={"is_active": False},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["is_active"] is False

    @pytest.mark.asyncio
    async def test_get_third_parties_auto_created_for_user(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that creating a user via API auto-creates a third party."""
        # Create user via API
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "tp_test_user",
                "name": "TP Test User",
                "email": "tp_test@test.com",
                "password": "TestPass123!",
                "role": "user",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        user_data = response.json()
        assert "third_party_id" in user_data

        # Verify third party was created
        result = await db_session.execute(
            select(ThirdParty).where(ThirdParty.id == user_data["third_party_id"])
        )
        tp = result.scalar_one_or_none()
        assert tp is not None
        assert tp.name == "TP Test User"


class TestGetThirdPartiesExclusionFlags:
    """Tests for GET /api/v1/third-parties exclusion flags."""

    @pytest.mark.asyncio
    async def test_exclude_patients(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test excluding third parties linked to patients."""
        # Create a third party linked to a patient
        tp_patient = ThirdParty(name="Patient TP", is_active=True)
        db_session.add(tp_patient)
        await db_session.flush()
        await db_session.refresh(tp_patient)
        patient = Patient(
            third_party_id=tp_patient.id,
        )
        db_session.add(patient)

        # Create a standalone third party (not linked to anything except admin user)
        tp_standalone = ThirdParty(name="Standalone TP", is_active=True)
        db_session.add(tp_standalone)
        await db_session.commit()

        # Without exclusion: both should appear
        response = await client.get("/api/v1/third-parties", headers=admin_headers)
        assert response.status_code == 200
        all_ids = {item["id"] for item in response.json()["items"]}
        assert tp_patient.id in all_ids
        assert tp_standalone.id in all_ids

        # With exclude_patients: patient's TP should be excluded
        response = await client.get(
            "/api/v1/third-parties",
            params={"exclude_patients": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        filtered_ids = {item["id"] for item in response.json()["items"]}
        assert tp_patient.id not in filtered_ids
        assert tp_standalone.id in filtered_ids

    @pytest.mark.asyncio
    async def test_exclude_doctors(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test excluding third parties linked to doctors."""
        tp_doctor = ThirdParty(name="Doctor TP", is_active=True)
        db_session.add(tp_doctor)
        await db_session.flush()
        await db_session.refresh(tp_doctor)
        doctor = Doctor(
            third_party_id=tp_doctor.id,
            name="Dr. Test", type="internal",
        )
        db_session.add(doctor)

        tp_standalone = ThirdParty(name="Standalone TP", is_active=True)
        db_session.add(tp_standalone)
        await db_session.commit()

        response = await client.get(
            "/api/v1/third-parties",
            params={"exclude_doctors": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        filtered_ids = {item["id"] for item in response.json()["items"]}
        assert tp_doctor.id not in filtered_ids
        assert tp_standalone.id in filtered_ids

    @pytest.mark.asyncio
    async def test_exclude_partners(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test excluding third parties linked to partners."""
        tp_partner = ThirdParty(name="Partner TP", is_active=True)
        db_session.add(tp_partner)
        await db_session.flush()
        await db_session.refresh(tp_partner)
        partner = Partner(
            third_party_id=tp_partner.id,
            name="Test Partner", partner_type="donor",
        )
        db_session.add(partner)

        tp_standalone = ThirdParty(name="Standalone TP", is_active=True)
        db_session.add(tp_standalone)
        await db_session.commit()

        response = await client.get(
            "/api/v1/third-parties",
            params={"exclude_partners": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        filtered_ids = {item["id"] for item in response.json()["items"]}
        assert tp_partner.id not in filtered_ids
        assert tp_standalone.id in filtered_ids

    @pytest.mark.asyncio
    async def test_exclude_users(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test excluding third parties linked to users."""
        # Admin user already has a third party, so it should be excluded
        tp_standalone = ThirdParty(name="Standalone TP", is_active=True)
        db_session.add(tp_standalone)
        await db_session.commit()
        await db_session.refresh(tp_standalone)

        response = await client.get(
            "/api/v1/third-parties",
            params={"exclude_users": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        filtered_ids = {item["id"] for item in response.json()["items"]}
        # Admin user's third party should be excluded
        assert admin_user.third_party_id not in filtered_ids
        assert tp_standalone.id in filtered_ids

    @pytest.mark.asyncio
    async def test_exclude_multiple_flags(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test combining multiple exclusion flags."""
        # Create a doctor TP
        tp_doctor = ThirdParty(name="Doctor TP", is_active=True)
        db_session.add(tp_doctor)
        await db_session.flush()
        await db_session.refresh(tp_doctor)
        doctor = Doctor(
            third_party_id=tp_doctor.id,
            name="Dr. Multi", type="internal",
        )
        db_session.add(doctor)

        # Create a patient TP
        tp_patient = ThirdParty(name="Patient TP", is_active=True)
        db_session.add(tp_patient)
        await db_session.flush()
        await db_session.refresh(tp_patient)
        patient = Patient(
            third_party_id=tp_patient.id,
        )
        db_session.add(patient)

        # Create a standalone TP
        tp_standalone = ThirdParty(name="Standalone TP", is_active=True)
        db_session.add(tp_standalone)
        await db_session.commit()

        response = await client.get(
            "/api/v1/third-parties",
            params={"exclude_doctors": True, "exclude_patients": True, "exclude_users": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        filtered_ids = {item["id"] for item in response.json()["items"]}
        assert tp_doctor.id not in filtered_ids
        assert tp_patient.id not in filtered_ids
        assert admin_user.third_party_id not in filtered_ids
        assert tp_standalone.id in filtered_ids

    @pytest.mark.asyncio
    async def test_exclude_flags_default_false(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that exclusion flags default to false (no exclusion)."""
        tp_doctor = ThirdParty(name="Doctor TP Default", is_active=True)
        db_session.add(tp_doctor)
        await db_session.flush()
        await db_session.refresh(tp_doctor)
        doctor = Doctor(
            third_party_id=tp_doctor.id,
            name="Dr. Default", type="internal",
        )
        db_session.add(doctor)
        await db_session.commit()

        # No exclusion flags set - doctor TP should still appear
        response = await client.get("/api/v1/third-parties", headers=admin_headers)
        assert response.status_code == 200
        all_ids = {item["id"] for item in response.json()["items"]}
        assert tp_doctor.id in all_ids


class TestGetThirdParty:
    """Tests for GET /api/v1/third-parties/{id}"""

    @pytest.mark.asyncio
    async def test_get_third_party_by_id(
        self, client: AsyncClient, admin_user: User, admin_headers: dict,
    ):
        """Test getting a third party by ID."""
        # The admin user's third_party_id
        tp_id = admin_user.third_party_id
        response = await client.get(
            f"/api/v1/third-parties/{tp_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tp_id
        assert data["name"] == "testadmin"

    @pytest.mark.asyncio
    async def test_get_third_party_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting non-existent third party."""
        response = await client.get(
            "/api/v1/third-parties/99999", headers=admin_headers
        )
        assert response.status_code == 404
