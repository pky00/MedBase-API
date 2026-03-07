"""Tests for third party endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.third_party import ThirdParty
from app.model.user import User


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
                "password": "testpass123",
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
