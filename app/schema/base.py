from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(from_attributes=True)


class AuditMixin(BaseModel):
    """Mixin for audit fields."""
    
    created_by: Optional[int] = None
    created_at: datetime
    updated_by: Optional[int] = None
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str
