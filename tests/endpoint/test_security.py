"""Tests for security features: token blacklist, password complexity, admin reset, refresh tokens, file validation."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user import User
from app.model.third_party import ThirdParty
from app.utility.security import get_password_hash, verify_password


async def _create_user(
    db_session: AsyncSession, username: str, email: str, password: str, role: str
) -> User:
    """Helper to create a user with its required third_party record."""
    tp = ThirdParty(name=username, email=email, is_active=True)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    user = User(
        third_party_id=tp.id,
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestTokenBlacklist:
    """Tests for server-side token invalidation on logout."""

    @pytest.mark.asyncio
    async def test_logout_invalidates_token(self, client: AsyncClient, admin_user: User):
        """After logout, the same token should be rejected."""
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify token works
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200

        # Logout
        response = await client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200

        # Token should now be rejected
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestRefreshToken:
    """Tests for refresh token functionality."""

    @pytest.mark.asyncio
    async def test_login_returns_refresh_token(self, client: AsyncClient, admin_user: User):
        """Login should return both access and refresh tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, admin_user: User):
        """Refresh token should return a new access+refresh token pair."""
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"},
        )
        refresh_token = response.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Invalid refresh token should be rejected."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_reuse_blocked(self, client: AsyncClient, admin_user: User):
        """Used refresh token should be blacklisted."""
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"},
        )
        refresh_token = response.json()["refresh_token"]

        # Use refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200

        # Try to reuse the same refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_access_token_cannot_refresh(self, client: AsyncClient, admin_user: User):
        """Access token should not be usable as a refresh token."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testadmin", "password": "TestPass123!"},
        )
        access_token = response.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == 401


class TestPasswordComplexity:
    """Tests for password complexity requirements."""

    @pytest.mark.asyncio
    async def test_create_user_weak_password_rejected(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Passwords without complexity should be rejected."""
        weak_passwords = [
            "short1",         # too short
            "alllowercase1!", # no uppercase
            "ALLUPPERCASE1!", # no lowercase
            "NoDigitsHere!",  # no digit
            "NoSpecial123",   # no special char
        ]
        for pw in weak_passwords:
            response = await client.post(
                "/api/v1/users",
                json={
                    "username": "weakuser",
                    "name": "Weak User",
                    "email": "weak@test.com",
                    "password": pw,
                    "role": "user",
                },
                headers=admin_headers,
            )
            assert response.status_code in (400, 422), f"Password '{pw}' should be rejected"

    @pytest.mark.asyncio
    async def test_create_user_strong_password_accepted(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Passwords meeting complexity requirements should be accepted."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "stronguser",
                "name": "Strong User",
                "email": "strong@test.com",
                "password": "StrongPass1!",
                "role": "user",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_update_user_weak_password_rejected(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Updating with a weak password should be rejected."""
        user = await _create_user(db_session, "pwupdate", "pwupdate@test.com", "TestPass123!", "user")

        response = await client.put(
            f"/api/v1/users/{user.id}",
            json={"password": "weak"},
            headers=admin_headers,
        )
        assert response.status_code in (400, 422)


class TestAdminPasswordReset:
    """Tests for admin password reset endpoint."""

    @pytest.mark.asyncio
    async def test_admin_reset_password_success(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Admin should be able to reset another user's password."""
        user = await _create_user(
            db_session, "resetme", "resetme@test.com", "OldPass123!", "user"
        )

        response = await client.post(
            "/api/v1/auth/admin/reset-password",
            json={"user_id": user.id, "new_password": "NewSecure1!"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"]

        # Verify old password no longer works
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "resetme", "password": "OldPass123!"},
        )
        assert response.status_code == 401

        # Verify new password works
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "resetme", "password": "NewSecure1!"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_reset_password_weak_rejected(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Admin reset with weak password should be rejected."""
        user = await _create_user(
            db_session, "resetweak", "resetweak@test.com", "OldPass123!", "user"
        )

        response = await client.post(
            "/api/v1/auth/admin/reset-password",
            json={"user_id": user.id, "new_password": "weak"},
            headers=admin_headers,
        )
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_admin_reset_password_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Reset password for non-existent user should return 404."""
        response = await client.post(
            "/api/v1/auth/admin/reset-password",
            json={"user_id": 99999, "new_password": "NewSecure1!"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_non_admin_cannot_reset_password(
        self, client: AsyncClient, user_headers: dict, db_session: AsyncSession
    ):
        """Non-admin user should not be able to reset passwords."""
        user = await _create_user(
            db_session, "target", "target@test.com", "OldPass123!", "user"
        )

        response = await client.post(
            "/api/v1/auth/admin/reset-password",
            json={"user_id": user.id, "new_password": "NewSecure1!"},
            headers=user_headers,
        )
        assert response.status_code == 403


class TestSecurityHeaders:
    """Tests for security headers in responses."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client: AsyncClient):
        """Security headers should be present in all responses."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "max-age" in response.headers.get("Strict-Transport-Security", "")


class TestGlobalExceptionHandler:
    """Tests for the global exception handler."""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_422(self, client: AsyncClient, admin_headers: dict):
        """Malformed requests should return proper error, not stack trace."""
        response = await client.post(
            "/api/v1/users",
            content="not valid json",
            headers={**admin_headers, "Content-Type": "application/json"},
        )
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
