from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class EquipmentCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(None, max_length=20)
    description: str | None = None
    parent_category_id: UUID | None = None
    is_active: bool = True


class EquipmentCategoryCreate(EquipmentCategoryBase):
    pass


class EquipmentCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, max_length=20)
    description: str | None = None
    parent_category_id: UUID | None = None
    is_active: bool | None = None


class EquipmentCategoryResponse(EquipmentCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EquipmentCategoryListResponse(BaseModel):
    data: list[EquipmentCategoryResponse]
    total: int

