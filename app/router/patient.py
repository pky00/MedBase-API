import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.patient import PatientService
from app.schema.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    Gender,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.patient")

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=PaginatedResponse[PatientResponse])
async def get_patients(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    gender: Optional[Gender] = Query(None, description="Filter by gender"),
    search: Optional[str] = Query(None, description="Search in first_name, last_name, phone, email"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all patients with pagination, filtering, and sorting."""
    logger.info("Listing patients page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = PatientService(db)
    patients, total = await service.get_all(
        page=page, size=size, is_active=is_active,
        gender=gender, search=search, sort=sort, order=order,
    )

    logger.info("Returning %d patients (total=%d)", len(patients), total)
    return PaginatedResponse(items=patients, total=total, page=page, size=size)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    with_documents: bool = Query(False, description="Include patient documents in response"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get patient by ID."""
    logger.info("Fetching patient_id=%d by user_id=%d", patient_id, current_user.id)

    service = PatientService(db)

    if with_documents:
        result = await service.get_by_id_with_documents(patient_id)
        if not result:
            logger.warning("Patient not found patient_id=%d", patient_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        patient, documents = result
        data = PatientResponse.model_validate(patient).model_dump()
        data["documents"] = documents
        return data

    patient = await service.get_by_id(patient_id)
    if not patient:
        logger.warning("Patient not found patient_id=%d", patient_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return patient


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new patient. Auto-creates a third_party record if third_party_id not provided."""
    logger.info(
        "Creating patient name='%s %s' by user_id=%d",
        data.first_name, data.last_name, current_user.id,
    )

    service = PatientService(db)

    # Check for duplicate name in patients table
    full_name = f"{data.first_name} {data.last_name}"
    existing = await service.get_by_name(data.first_name, data.last_name)
    if existing:
        logger.warning("Patient name already exists name='%s'", full_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient name already exists",
        )

    # Check for duplicate name in third_parties table
    from app.service.third_party import ThirdPartyService
    tp_service = ThirdPartyService(db)
    existing_tp = await tp_service.get_by_name(full_name)
    if existing_tp:
        logger.warning("Name already exists in third parties name='%s'", full_name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name already exists in third parties",
        )

    # Validate third_party_id if provided
    if data.third_party_id:
        tp = await tp_service.get_by_id(data.third_party_id)
        if not tp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Third party not found")

    patient = await service.create(data, created_by=current_user.username)
    logger.info("Patient created patient_id=%d", patient.id)
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a patient."""
    logger.info("Updating patient_id=%d by user_id=%d", patient_id, current_user.id)

    service = PatientService(db)

    patient = await service.get_by_id(patient_id)
    if not patient:
        logger.warning("Patient not found for update patient_id=%d", patient_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    updated = await service.update(patient_id, data, updated_by=current_user.username)
    logger.info("Patient updated patient_id=%d", patient_id)
    return updated


@router.delete("/{patient_id}", response_model=MessageResponse)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a patient (soft delete)."""
    logger.info("Deleting patient_id=%d by user_id=%d", patient_id, current_user.id)

    service = PatientService(db)

    patient = await service.get_by_id(patient_id)
    if not patient:
        logger.warning("Patient not found for deletion patient_id=%d", patient_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    await service.delete(patient_id, deleted_by=current_user.username)
    logger.info("Patient deleted patient_id=%d", patient_id)
    return MessageResponse(message="Patient deleted successfully")
