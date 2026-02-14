import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.security import decode_access_token
from app.model.user import User
from app.service.user import UserService
from app.schema.enums import UserRole

logger = logging.getLogger("medbase.utility.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    logger.info("Authenticating token (first 20 chars): %s...", token[:20] if len(token) > 20 else token)
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Token decode failed - invalid or expired token")
        raise credentials_exception
    
    logger.info("Token payload: sub=%s username=%s", payload.get("sub"), payload.get("username"))
    user_id_str = payload.get("sub")
    if user_id_str is None:
        logger.warning("No 'sub' claim in token payload")
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.warning("Invalid 'sub' claim format: %s", user_id_str)
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if user is None:
        logger.warning("User not found in database for id=%s", user_id)
        raise credentials_exception
    
    if not user.is_active:
        logger.warning("User account is inactive id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
