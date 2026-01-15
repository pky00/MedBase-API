import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.security import verify_password, create_access_token

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Authenticate user by username and password.
        Returns User if valid, None otherwise.
        """
        logger.info(f"Authentication attempt for user: {username}")
        
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Authentication failed: user not found: {username}")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: invalid password for user: {username}")
            return None
        
        logger.info(f"Authentication successful for user: {username}")
        return user
    
    async def update_last_login(self, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Updated last login for user: {user.username}")
    
    def create_token(self, username: str) -> str:
        """Create JWT access token for user."""
        logger.info(f"Creating access token for user: {username}")
        return create_access_token(data={"sub": username})
