"""Patient management endpoints."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
)
from app.services.patient_service import PatientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new patient.
    
    Patient number is auto-generated in format P000001, P000002, etc.
    """
    logger.info(f"Creating patient request from user: {current_user.username}")
    
    patient_service = PatientService(db)
    
    # Check for duplicate email if provided
    if patient_data.email:
        existing = await patient_service.get_by_email(patient_data.email)
        if existing:
            logger.warning(f"Duplicate email attempt: {patient_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this email already exists"
            )
    
    # Check for duplicate national ID if provided
    if patient_data.national_id:
        existing = await patient_service.get_by_national_id(patient_data.national_id)
        if existing:
            logger.warning(f"Duplicate national ID attempt: {patient_data.national_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this national ID already exists"
            )
    
    patient = await patient_service.create(patient_data)
    return patient


@router.get("/", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name, patient number, phone, or email"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of patients.
    
    Supports search by patient_number, first_name, last_name, phone, or email.
    """
    logger.info(f"Listing patients request from user: {current_user.username}")
    
    patient_service = PatientService(db)
    patients, total = await patient_service.list_patients(
        page=page,
        size=size,
        search=search
    )
    
    return PatientListResponse(
        data=patients,
        total=total,
        page=page,
        size=size
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a patient by ID."""
    logger.info(f"Get patient request: {patient_id} from user: {current_user.username}")
    
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.get("/number/{patient_number}", response_model=PatientResponse)
async def get_patient_by_number(
    patient_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a patient by patient number."""
    logger.info(f"Get patient by number request: {patient_number} from user: {current_user.username}")
    
    patient_service = PatientService(db)
    patient = await patient_service.get_by_patient_number(patient_number)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a patient."""
    logger.info(f"Update patient request: {patient_id} from user: {current_user.username}")
    
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check for duplicate email if updating email
    if patient_data.email and patient_data.email != patient.email:
        existing = await patient_service.get_by_email(patient_data.email)
        if existing and existing.id != patient_id:
            logger.warning(f"Duplicate email attempt: {patient_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this email already exists"
            )
    
    # Check for duplicate national ID if updating
    if patient_data.national_id and patient_data.national_id != patient.national_id:
        existing = await patient_service.get_by_national_id(patient_data.national_id)
        if existing and existing.id != patient_id:
            logger.warning(f"Duplicate national ID attempt: {patient_data.national_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this national ID already exists"
            )
    
    updated_patient = await patient_service.update(patient, patient_data)
    return updated_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a patient."""
    logger.info(f"Delete patient request: {patient_id} from user: {current_user.username}")
    
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    
    if not patient:
        logger.warning(f"Patient not found: {patient_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    await patient_service.delete(patient)

