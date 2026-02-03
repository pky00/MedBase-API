"""Tests for User model and database operations."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.model.user import User
from app.service.user import UserService
from app.schema.user import UserCreate, UserUpdate
from app.utility.security import verify_password


class TestUserModel:
    """Tests for User SQLAlchemy model."""
    
    @pytest.mark.asyncio
    async def test_create_user_in_db(self, db_session: AsyncSession):
        """Test creating a user directly in database."""
        from app.utility.security import get_password_hash
        
        user = User(
            username="testuser",
            email="test@test.com",
            password_hash=get_password_hash("testpass"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.is_deleted is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_password_hashing(self, db_session: AsyncSession):
        """Test that password is properly hashed."""
        from app.utility.security import get_password_hash
        
        plain_password = "mysecretpassword"
        user = User(
            username="hashtest",
            email="hash@test.com",
            password_hash=get_password_hash(plain_password),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Password should not be stored in plain text
        assert user.password_hash != plain_password
        # But should verify correctly
        assert verify_password(plain_password, user.password_hash) is True
        assert verify_password("wrongpassword", user.password_hash) is False


class TestUserService:
    """Tests for UserService."""
    
    @pytest.mark.asyncio
    async def test_service_create_user(self, db_session: AsyncSession):
        """Test creating user via service."""
        service = UserService(db_session)
        user_data = UserCreate(
            username="serviceuser",
            email="service@test.com",
            password="servicepass",
            role="user",
        )
        
        user = await service.create(user_data)
        await db_session.commit()
        
        assert user.id is not None
        assert user.username == "serviceuser"
        assert verify_password("servicepass", user.password_hash) is True
    
    @pytest.mark.asyncio
    async def test_service_get_by_id(self, db_session: AsyncSession):
        """Test getting user by ID via service."""
        from app.utility.security import get_password_hash
        
        # Create user
        user = User(
            username="getbyid",
            email="getbyid@test.com",
            password_hash=get_password_hash("test"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        service = UserService(db_session)
        found = await service.get_by_id(user.id)
        
        assert found is not None
        assert found.id == user.id
        assert found.username == "getbyid"
    
    @pytest.mark.asyncio
    async def test_service_get_by_username(self, db_session: AsyncSession):
        """Test getting user by username via service."""
        from app.utility.security import get_password_hash
        
        user = User(
            username="findme",
            email="findme@test.com",
            password_hash=get_password_hash("test"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        
        service = UserService(db_session)
        found = await service.get_by_username("findme")
        
        assert found is not None
        assert found.username == "findme"
    
    @pytest.mark.asyncio
    async def test_service_update_user(self, db_session: AsyncSession):
        """Test updating user via service."""
        from app.utility.security import get_password_hash
        
        user = User(
            username="toupdate",
            email="toupdate@test.com",
            password_hash=get_password_hash("test"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        service = UserService(db_session)
        update_data = UserUpdate(username="updated", email="updated@test.com")
        updated = await service.update(user.id, update_data)
        await db_session.commit()
        
        assert updated is not None
        assert updated.username == "updated"
        assert updated.email == "updated@test.com"
    
    @pytest.mark.asyncio
    async def test_service_soft_delete(self, db_session: AsyncSession):
        """Test soft delete via service."""
        from app.utility.security import get_password_hash
        
        user = User(
            username="todelete",
            email="todelete@test.com",
            password_hash=get_password_hash("test"),
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        service = UserService(db_session)
        result = await service.delete(user.id)
        await db_session.commit()
        
        assert result is True
        
        # User should still exist but be marked as deleted
        result = await db_session.execute(
            select(User).where(User.id == user.id)
        )
        deleted_user = result.scalar_one()
        assert deleted_user.is_deleted is True
        
        # Service should not find deleted user
        found = await service.get_by_id(user.id)
        assert found is None
    
    @pytest.mark.asyncio
    async def test_service_authenticate(self, db_session: AsyncSession):
        """Test user authentication via service."""
        service = UserService(db_session)
        user_data = UserCreate(
            username="authuser",
            email="auth@test.com",
            password="authpass123",
            role="user",
        )
        
        await service.create(user_data)
        await db_session.commit()
        
        # Successful authentication
        user = await service.authenticate("authuser", "authpass123")
        assert user is not None
        assert user.username == "authuser"
        
        # Failed authentication - wrong password
        user = await service.authenticate("authuser", "wrongpass")
        assert user is None
        
        # Failed authentication - non-existent user
        user = await service.authenticate("nouser", "anypass")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_service_get_all_pagination(self, db_session: AsyncSession):
        """Test getting all users with pagination."""
        from app.utility.security import get_password_hash
        
        # Create multiple users
        for i in range(15):
            user = User(
                username=f"paginationuser{i}",
                email=f"pagination{i}@test.com",
                password_hash=get_password_hash("test"),
                role="user" if i % 2 == 0 else "admin",
            )
            db_session.add(user)
        await db_session.commit()
        
        service = UserService(db_session)
        
        # Test pagination
        users, total = await service.get_all(page=1, size=5)
        assert len(users) == 5
        assert total == 15
        
        # Test filtering
        users, total = await service.get_all(role="admin")
        assert all(u.role == "admin" for u in users)
