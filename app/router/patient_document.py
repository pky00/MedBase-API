import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.patient import PatientService
from app.service.patient_document import PatientDocumentService, document_to_response
from app.schema.patient_document import PatientDocumentResponse, PatientDocumentType
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.patient_document")

router = APIRouter(tags=["Patient Documents"])


@router.get("/patient-document-types", response_model=list[dict])
async def get_patient_document_types(
    current_user: User = Depends(get_current_user),
):
    """Return all available patient document types."""
    logger.info("Listing patient document types by user_id=%d", current_user.id)
    return [{"value": t.value, "label": t.value.replace("_", " ").title()} for t in PatientDocumentType]


@router.get(
    "/patients/{patient_id}/documents",
    response_model=PaginatedResponse[PatientDocumentResponse],
)
async def get_patient_documents(
    patient_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents for a patient."""
    logger.info("Listing documents for patient_id=%d by user_id=%d", patient_id, current_user.id)

    # Verify patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    service = PatientDocumentService(db)
    documents, total = await service.get_all_for_patient(
        patient_id=patient_id, page=page, size=size,
        document_type=document_type, sort=sort, order=order,
    )

    items = [await document_to_response(doc) for doc in documents]

    logger.info("Returning %d documents (total=%d) for patient_id=%d", len(documents), total, patient_id)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/patient-documents/{document_id}", response_model=PatientDocumentResponse)
async def get_patient_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document by ID."""
    logger.info("Fetching document_id=%d by user_id=%d", document_id, current_user.id)

    service = PatientDocumentService(db)
    doc = await service.get_by_id(document_id)

    if not doc:
        logger.warning("Document not found document_id=%d", document_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return await document_to_response(doc)


@router.post(
    "/patients/{patient_id}/documents",
    response_model=PatientDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_patient_document(
    patient_id: int,
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None, description="Custom display name for the document"),
    document_type: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for a patient. Accepts multipart/form-data."""
    logger.info(
        "Uploading document for patient_id=%d filename='%s' by user_id=%d",
        patient_id, file.filename, current_user.id,
    )

    # Validate file type
    ALLOWED_EXTENSIONS = {
        "pdf", "jpg", "jpeg", "png", "gif", "bmp", "webp",
        "doc", "docx", "xls", "xlsx", "csv", "txt", "rtf",
        "dicom", "dcm",
    }
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv", "text/plain", "application/rtf",
        "application/dicom", "application/octet-stream",
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{ext}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type '{file.content_type}' is not allowed",
        )

    # Validate file size by reading and checking length
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )
    # Reset file position so the service can read it again
    await file.seek(0)

    # Verify patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    service = PatientDocumentService(db)
    doc = await service.upload(
        patient_id=patient_id,
        file=file,
        document_name=document_name,
        document_type=document_type,
        created_by=current_user.username,
    )

    logger.info("Document uploaded document_id=%d patient_id=%d", doc.id, patient_id)
    return await document_to_response(doc)


@router.delete("/patient-documents/{document_id}", response_model=MessageResponse)
async def delete_patient_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a patient document (soft delete)."""
    logger.info("Deleting document_id=%d by user_id=%d", document_id, current_user.id)

    service = PatientDocumentService(db)

    doc = await service.get_by_id(document_id)
    if not doc:
        logger.warning("Document not found for deletion document_id=%d", document_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await service.delete(document_id, deleted_by=current_user.username)
    logger.info("Document deleted document_id=%d", document_id)
    return MessageResponse(message="Document deleted successfully")
