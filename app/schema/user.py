from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRole(str, Enum):
    """User role values."""

    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    """Base schema for user data."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name for third party record")
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (without password)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    third_party_id: int
    role: str
    is_active: bool
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime


class UserInDB(UserResponse):
    """Schema for user stored in database."""
    
    password_hash: str
