from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MedicineCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(None, max_length=20)
    description: str | None = None
    parent_category_id: UUID | None = None


class MedicineCategoryCreate(MedicineCategoryBase):
    pass


class MedicineCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, max_length=20)
    description: str | None = None
    parent_category_id: UUID | None = None


class MedicineCategoryResponse(MedicineCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MedicineCategoryListResponse(BaseModel):
    data: list[MedicineCategoryResponse]
    total: int

