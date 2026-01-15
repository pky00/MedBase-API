from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.enums import DocumentType
from app.schemas.patient_document import (
    PatientDocumentCreate,
    PatientDocumentUpdate,
    PatientDocumentResponse,
    PatientDocumentListResponse,
)
from app.services.patient_document_service import PatientDocumentService
from app.services.patient_service import PatientService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/patients/{patient_id}/documents", tags=["patient-documents"])


@router.post("/", response_model=PatientDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    patient_id: UUID,
    document_data: PatientDocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for a patient."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Override patient_id from path
    document_data.patient_id = patient_id

    service = PatientDocumentService(db)
    return await service.create(document_data, created_by=current_user.username)


@router.get("/", response_model=PatientDocumentListResponse)
async def list_documents(
    patient_id: UUID,
    document_type: DocumentType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for a patient."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    service = PatientDocumentService(db)
    documents, total = await service.list_by_patient(patient_id, document_type=document_type)
    return PatientDocumentListResponse(data=documents, total=total)


@router.get("/{document_id}", response_model=PatientDocumentResponse)
async def get_document(
    patient_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    service = PatientDocumentService(db)
    document = await service.get_by_id(document_id)
    if not document or document.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.patch("/{document_id}", response_model=PatientDocumentResponse)
async def update_document(
    patient_id: UUID,
    document_id: UUID,
    document_data: PatientDocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a document."""
    service = PatientDocumentService(db)
    document = await service.get_by_id(document_id)
    if not document or document.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return await service.update(document, document_data, updated_by=current_user.username)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    patient_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    service = PatientDocumentService(db)
    document = await service.get_by_id(document_id)
    if not document or document.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    await service.delete(document)

