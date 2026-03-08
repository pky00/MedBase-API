from datetime import date, datetime
from enum import StrEnum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.schema.patient_document import PatientDocumentResponse
from app.schema.third_party import ThirdPartyResponse


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class PatientCreate(BaseModel):
    """Schema for creating a patient."""

    third_party_id: Optional[int] = None
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=255)
    emergency_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class PatientResponse(BaseModel):
    """Schema for patient response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    third_party_id: int
    third_party: Optional[ThirdPartyResponse] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    is_active: bool
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime
    documents: Optional[List[PatientDocumentResponse]] = None
