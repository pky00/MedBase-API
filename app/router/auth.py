import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    validate_password_strength,
)
from app.utility.auth import get_current_user, get_current_admin_user, oauth2_scheme
from app.utility.token_blacklist import token_blacklist
from app.utility.rate_limit import limiter
from app.service.user import UserService
from app.schema.auth import Token, TokenRefreshRequest, AdminPasswordReset
from app.schema.user import UserResponse
from app.schema.base import MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT access and refresh tokens.

    - **username**: Username
    - **password**: Password

    Returns access token (1 hour) and refresh token (7 days).
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

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    logger.info("Login successful for user_id=%d username='%s'", user.id, user.username)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
):
    """
    Logout current user by invalidating their token server-side.

    The token is added to a blacklist and will be rejected on future requests.
    """
    payload = decode_access_token(token)
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp", 0)
        if jti:
            token_blacklist.add(jti, exp)
            # Clean up expired entries periodically
            token_blacklist.cleanup()

    logger.info("User logged out user_id=%d", current_user.id)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a new access token using a valid refresh token.

    The old refresh token is invalidated and a new pair is returned.
    """
    payload = decode_access_token(body.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Check if refresh token was blacklisted
    jti = payload.get("jti")
    if jti and token_blacklist.is_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user_service = UserService(db)
    user = await user_service.get_by_id(int(user_id_str))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Blacklist old refresh token
    if jti:
        token_blacklist.add(jti, payload.get("exp", 0))

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    }
    new_access = create_access_token(data=token_data)
    new_refresh = create_refresh_token(data=token_data)

    logger.info("Token refreshed for user_id=%d", user.id)
    return Token(access_token=new_access, refresh_token=new_refresh)


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


@router.post("/admin/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def admin_reset_password(
    request: Request,
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Reset a user's password. **Admin only.**

    The admin specifies the target user ID and the new password.
    Password must meet complexity requirements.
    """
    logger.info(
        "Admin password reset for user_id=%d by admin_id=%d",
        body.user_id, current_user.id,
    )

    # Validate password strength
    error = validate_password_strength(body.new_password)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    user_service = UserService(db)
    user = await user_service.get_by_id(body.user_id)
    if not user:
        logger.warning("User not found for password reset user_id=%d", body.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await user_service.reset_password(body.user_id, body.new_password, updated_by=current_user.username)
    logger.info("Password reset successful for user_id=%d", body.user_id)
    return MessageResponse(message="Password reset successfully")
