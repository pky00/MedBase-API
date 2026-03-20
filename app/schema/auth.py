from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data encoded in token."""

    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class AdminPasswordReset(BaseModel):
    """Schema for admin password reset."""

    user_id: int = Field(..., description="ID of the user whose password to reset")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
