from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.model.base import BaseModel


class PatientDocument(BaseModel):
    """Model for patient document records."""

    __tablename__ = "patient_documents"

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    document_name = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, server_default=func.now(), nullable=False)
