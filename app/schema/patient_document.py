from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


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
