"""Tests for user endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.third_party import ThirdParty
from app.model.user import User
from app.utility.security import verify_password


async def _create_test_user(
    db_session: AsyncSession, username: str, email: str, password: str, role: str, is_active: bool = True
) -> User:
    """Helper to create a user with its required third_party record."""
    from app.utility.security import get_password_hash

    tp = ThirdParty(name=username, email=email, is_active=is_active)
    db_session.add(tp)
    await db_session.flush()
    await db_session.refresh(tp)

    user = User(
        third_party_id=tp.id,
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetUsers:
    """Tests for GET /api/v1/users"""
    
    @pytest.mark.asyncio
    async def test_get_users_as_admin(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting users list as admin."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_get_users_as_regular_user(self, client: AsyncClient, user_headers: dict):
        """Test getting users list as regular user (should fail)."""
        response = await client.get(
            "/api/v1/users",
            headers=user_headers
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_users_unauthenticated(self, client: AsyncClient):
        """Test getting users list without authentication."""
        response = await client.get("/api/v1/users")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_users_with_filters(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting users with filters."""
        response = await client.get(
            "/api/v1/users",
            params={"role": "admin", "is_active": True},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for user in data["items"]:
            assert user["role"] == "admin"
            assert user["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_users_pagination(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test users pagination."""
        response = await client.get(
            "/api/v1/users",
            params={"page": 1, "size": 5},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test getting user by ID."""
        response = await client.get(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id
        assert data["username"] == admin_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/users/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestCreateUser:
    """Tests for POST /api/v1/users"""
    
    @pytest.mark.asyncio
    async def test_create_user_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating a new user and verify in database."""
        user_data = {
            "username": "newuser",
            "name": "New User",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "user",
            "is_active": True
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        # Verify API response
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert "password" not in data
        assert "password_hash" not in data
        
        # Verify database state
        result = await db_session.execute(
            select(User).where(User.id == data["id"])
        )
        db_user = result.scalar_one_or_none()
        
        assert db_user is not None
        assert db_user.username == "newuser"
        assert db_user.email == "newuser@test.com"
        assert db_user.role == "user"
        assert db_user.is_active is True
        assert db_user.is_deleted is False
        assert db_user.created_by == admin_user.username
        assert db_user.updated_by == admin_user.username
        assert verify_password("newpass123", db_user.password_hash) is True
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test creating user with duplicate username."""
        user_data = {
            "username": "testadmin",  # Already exists
            "name": "Another Name",
            "email": "another@test.com",
            "password": "newpass123",
            "role": "user"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test creating user with duplicate email."""
        user_data = {
            "username": "newusername",
            "name": "New Username",
            "email": "testadmin@test.com",  # Already exists
            "password": "newpass123",
            "role": "user"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_user_third_party_uses_name(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test that third_party record uses name field instead of username."""
        user_data = {
            "username": "tpnameuser",
            "name": "Third Party Full Name",
            "email": "tpname@test.com",
            "password": "testpass123",
            "role": "user"
        }

        response = await client.post("/api/v1/users", json=user_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()

        # Verify third_party uses the name field
        result = await db_session.execute(
            select(ThirdParty).where(ThirdParty.id == data["third_party_id"])
        )
        tp = result.scalar_one_or_none()
        assert tp is not None
        assert tp.name == "Third Party Full Name"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_name_in_third_parties(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test creating user with name that already exists in third_parties fails."""
        # Create a third_party with a specific name
        tp = ThirdParty(name="Existing TP Name", is_active=True)
        db_session.add(tp)
        await db_session.commit()

        user_data = {
            "username": "uniqueuser",
            "name": "Existing TP Name",
            "email": "unique@test.com",
            "password": "testpass123",
            "role": "user"
        }

        response = await client.post("/api/v1/users", json=user_data, headers=admin_headers)
        assert response.status_code == 400
        assert "already exists in third parties" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_invalid_role(self, client: AsyncClient, admin_headers: dict):
        """Test creating user with invalid role."""
        user_data = {
            "username": "newuser",
            "name": "New User",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "invalid_role"
        }
        
        response = await client.post(
            "/api/v1/users",
            json=user_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_update_user_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating a user and verify in database."""
        admin_username = admin_user.username  # Save before expire_all

        # Create a user to update
        user = await _create_test_user(db_session, "toupdate", "toupdate@test.com", "testpass123", "user")
        user_id = user.id
        
        update_data = {
            "username": "updated",
            "email": "updated@test.com"
        }
        
        response = await client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            headers=admin_headers
        )
        
        # Verify API response
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updated"
        assert data["email"] == "updated@test.com"
        
        # Verify database state
        db_session.expire_all()
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        
        assert db_user is not None
        assert db_user.username == "updated"
        assert db_user.email == "updated@test.com"
        assert db_user.updated_by == admin_username
    
    @pytest.mark.asyncio
    async def test_update_user_password(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test updating user password and verify in database."""
        # Create a user to update
        user = await _create_test_user(db_session, "passupdate", "passupdate@test.com", "oldpass123", "user")
        user_id = user.id
        
        update_data = {"password": "newpass456"}
        
        response = await client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        
        # Verify password was updated in database
        db_session.expire_all()
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        
        assert db_user is not None
        assert verify_password("newpass456", db_user.password_hash) is True
        assert verify_password("oldpass123", db_user.password_hash) is False
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent user."""
        response = await client.put(
            "/api/v1/users/99999",
            json={"username": "test"},
            headers=admin_headers
        )
        
        assert response.status_code == 404


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{user_id}"""
    
    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, client: AsyncClient, admin_user: User, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting a user (soft delete) and verify in database."""
        admin_username = admin_user.username  # Save before expire_all

        # Create a user to delete
        user = await _create_test_user(db_session, "todelete", "todelete@test.com", "testpass123", "user")
        user_id = user.id
        
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_headers
        )
        
        # Verify API response
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify database state - user should still exist but be soft deleted
        db_session.expire_all()
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        
        assert db_user is not None
        assert db_user.is_deleted is True
        assert db_user.updated_by == admin_username
    
    @pytest.mark.asyncio
    async def test_delete_self_forbidden(self, client: AsyncClient, admin_user: User, admin_headers: dict):
        """Test admin cannot delete themselves."""
        response = await client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "cannot delete themselves" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test deleting non-existent user."""
        response = await client.delete(
            "/api/v1/users/99999",
            headers=admin_headers
        )
        
        assert response.status_code == 404
