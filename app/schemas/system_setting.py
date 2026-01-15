from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SystemSettingBase(BaseModel):
    setting_key: str = Field(..., min_length=1, max_length=100)
    setting_value: str | None = None
    setting_type: str = Field("string", max_length=50)
    category: str | None = Field(None, max_length=100)
    description: str | None = None
    is_public: bool = False
    is_editable: bool = True


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    setting_value: str | None = None
    setting_type: str | None = Field(None, max_length=50)
    category: str | None = Field(None, max_length=100)
    description: str | None = None
    is_public: bool | None = None
    is_editable: bool | None = None


class SystemSettingResponse(SystemSettingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemSettingListResponse(BaseModel):
    data: list[SystemSettingResponse]
    total: int

