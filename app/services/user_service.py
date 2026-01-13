from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password
from app.utils.context import get_audit_user


class UserService:
    """Service for user CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def list_users(self, page: int = 1, per_page: int = 20) -> tuple[list[User], int]:
        """
        Get paginated list of users.
        Returns tuple of (users, total_count).
        """
        # Count total
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar()
        
        # Get paginated users
        offset = (page - 1) * per_page
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        users = list(result.scalars().all())
        
        return users, total
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user. Uses current user from context for audit."""
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            created_by=get_audit_user(),
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user
    
    async def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user with provided data. Uses current user from context for audit."""
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_by = get_audit_user()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(self, user: User, new_password: str) -> None:
        """Change user's password. Uses current user from context for audit."""
        user.password_hash = get_password_hash(new_password)
        user.updated_by = get_audit_user()
        await self.db.commit()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return verify_password(plain_password, hashed_password)
    
    async def delete(self, user: User) -> None:
        """Delete a user."""
        await self.db.delete(user)
        await self.db.commit()

