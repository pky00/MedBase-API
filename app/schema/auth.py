from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    username: str
    password: str


class Token(BaseModel):
    """Schema for access token response."""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data encoded in token."""
    
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
