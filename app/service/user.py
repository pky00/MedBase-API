import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import contains_eager

from app.model.user import User
from app.model.third_party import ThirdParty
from app.schema.user import UserCreate, UserUpdate
from app.utility.security import get_password_hash, verify_password
from app.service.third_party import ThirdPartyService

logger = logging.getLogger("medbase.service.user")


class UserService:
    """Service layer for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User)
            .outerjoin(ThirdParty, User.third_party_id == ThirdParty.id)
            .options(contains_eager(User.third_party))
            .where(User.id == user_id, User.is_deleted == False)
        )
        return result.unique().scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (via third_party)."""
        result = await self.db.execute(
            select(User)
            .outerjoin(ThirdParty, User.third_party_id == ThirdParty.id)
            .options(contains_eager(User.third_party))
            .where(ThirdParty.email == email, User.is_deleted == False)
        )
        return result.unique().scalar_one_or_none()

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
        query = (
            select(User)
            .outerjoin(ThirdParty, User.third_party_id == ThirdParty.id)
            .options(contains_eager(User.third_party))
            .where(User.is_deleted == False)
        )

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
                    ThirdParty.email.ilike(search_term)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        tp_sort_map = {"email": ThirdParty.email, "name": ThirdParty.name}
        sort_column = tp_sort_map.get(sort, getattr(User, sort, User.id))
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        users = result.unique().scalars().all()

        logger.debug("Queried users: total=%d returned=%d", total, len(users))

        return list(users), total

    async def create(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create a new user. Auto-creates a third_party record if third_party_id not provided."""
        tp_service = ThirdPartyService(self.db)

        if user_data.third_party_id:
            tp = await tp_service.get_by_id(user_data.third_party_id)
            if not tp:
                raise ValueError("Third party not found")
            third_party_id = user_data.third_party_id
        else:
            tp = await tp_service.create(
                name=user_data.name,
                email=user_data.email,
                is_active=user_data.is_active,
                created_by=created_by,
            )
            third_party_id = tp.id

        user = User(
            third_party_id=third_party_id,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        user.third_party = tp
        logger.info("Created user id=%d username='%s' third_party_id=%d", user.id, user.username, third_party_id)
        return user

    async def update(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: Optional[str] = None
    ) -> Optional[User]:
        """Update an existing user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)

        # Separate third_party fields
        tp_fields = {}
        for field in ("name", "email"):
            if field in update_data:
                tp_fields[field] = update_data.pop(field)

        # Hash password if provided
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        # Update user fields
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_by = updated_by

        # Update third_party if needed
        if tp_fields:
            tp_service = ThirdPartyService(self.db)
            await tp_service.update(user.third_party_id, **tp_fields, updated_by=updated_by)

        await self.db.flush()
        logger.info("Updated user id=%d fields=%s", user_id, list(user_data.model_dump(exclude_unset=True).keys()))
        return await self.get_by_id(user_id)

    async def delete(self, user_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.is_deleted = True
        user.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted user id=%d", user_id)
        return True

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = await self.get_by_username(username)
        if not user:
            logger.debug("Auth failed: user not found username='%s'", username)
            return None
        if not user.is_active:
            logger.debug("Auth failed: user inactive username='%s'", username)
            return None
        if not verify_password(password, user.password_hash):
            logger.debug("Auth failed: wrong password username='%s'", username)
            return None
        return user
