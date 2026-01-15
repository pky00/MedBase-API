from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import DocumentType


class PatientDocumentBase(BaseModel):
    patient_id: UUID
    medical_record_id: UUID | None = None
    appointment_id: UUID | None = None
    document_type: DocumentType
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    file_path: str = Field(..., min_length=1)
    file_hash: str | None = Field(None, max_length=64)
    document_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None


class PatientDocumentCreate(PatientDocumentBase):
    pass


class PatientDocumentUpdate(BaseModel):
    medical_record_id: UUID | None = None
    appointment_id: UUID | None = None
    document_type: DocumentType | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    file_path: str | None = Field(None, min_length=1)
    file_hash: str | None = Field(None, max_length=64)
    document_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None


class PatientDocumentResponse(PatientDocumentBase):
    id: UUID
    upload_date: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PatientDocumentListResponse(BaseModel):
    data: list[PatientDocumentResponse]
    total: int

