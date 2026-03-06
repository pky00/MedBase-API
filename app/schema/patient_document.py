from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PatientDocumentType(StrEnum):
    LAB_REPORT = "lab_report"
    IMAGING = "imaging"
    PRESCRIPTION = "prescription"
    REFERRAL = "referral"
    INSURANCE = "insurance"
    IDENTIFICATION = "identification"
    CONSENT_FORM = "consent_form"
    MEDICAL_HISTORY = "medical_history"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"


class PatientDocumentResponse(BaseModel):
    """Schema for patient document response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    document_name: str
    document_type: Optional[str] = None
    file_path: str
    file_url: Optional[str] = None
    upload_date: datetime
    is_deleted: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: datetime

    @classmethod
    def from_model(cls, doc, file_url: str) -> "PatientDocumentResponse":
        """Build from a PatientDocument model with resolved file_url."""
        return cls.model_validate(
            {
                "id": doc.id,
                "patient_id": doc.patient_id,
                "document_name": doc.document_name,
                "document_type": doc.document_type,
                "file_path": doc.file_path,
                "file_url": file_url,
                "upload_date": doc.upload_date,
                "is_deleted": doc.is_deleted,
                "created_by": doc.created_by,
                "created_at": doc.created_at,
                "updated_by": doc.updated_by,
                "updated_at": doc.updated_at,
            }
        )
