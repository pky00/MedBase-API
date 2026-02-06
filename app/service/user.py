from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.user import User
from app.schema.user import UserCreate, UserUpdate
from app.utility.security import get_password_hash, verify_password


class UserService:
    """Service layer for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc"
    ) -> Tuple[List[User], int]:
        """Get all users with pagination, filtering, and sorting."""
        query = select(User).where(User.is_deleted == False)
        
        # Apply filters
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(User, sort, User.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create(self, user_data: UserCreate, created_by: Optional[int] = None) -> User:
        """Create a new user."""
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: Optional[int] = None
    ) -> Optional[User]:
        """Update an existing user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        # Update fields
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_deleted = True
        user.updated_by = deleted_by
        await self.db.flush()
        return True
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
