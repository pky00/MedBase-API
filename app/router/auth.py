import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.security import create_access_token
from app.utility.auth import get_current_user
from app.service.user import UserService
from app.schema.auth import LoginRequest, Token
from app.schema.user import UserResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    - **username**: Username
    - **password**: Password
    
    Returns access token on success.
    Token expires after 1 hour.
    """
    logger.info("Login attempt for username='%s'", form_data.username)
    
    user_service = UserService(db)
    user = await user_service.authenticate(form_data.username, form_data.password)
    
    if not user:
        logger.warning("Login failed for username='%s'", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        }
    )
    
    logger.info("Login successful for user_id=%d username='%s'", user.id, user.username)
    return Token(access_token=access_token)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: JWT tokens are stateless, so this endpoint just confirms
    the logout action. The client should discard the token.
    """
    logger.info("User logged out user_id=%d", current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Returns user details without password.
    """
    logger.info("Fetching current user info user_id=%d", current_user.id)
    return current_user
