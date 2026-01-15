from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordUpdate,
    MedicalRecordResponse,
    MedicalRecordListResponse,
)
from app.services.medical_record_service import MedicalRecordService
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/medical-records", tags=["medical-records"])


@router.post("/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new medical record."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(record_data.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not found",
        )

    # Validate doctor exists
    doctor_service = DoctorService(db)
    doctor = await doctor_service.get_by_id(record_data.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor not found",
        )

    service = MedicalRecordService(db)
    return await service.create(record_data, created_by=current_user.username)


@router.get("/", response_model=MedicalRecordListResponse)
async def list_medical_records(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    patient_id: UUID | None = None,
    doctor_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all medical records with pagination and filtering."""
    service = MedicalRecordService(db)
    records, total = await service.list_records(
        page=page,
        size=size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        date_from=date_from,
        date_to=date_to,
    )
    return MedicalRecordListResponse(data=records, total=total, page=page, size=size)


@router.get("/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific medical record by ID."""
    service = MedicalRecordService(db)
    record = await service.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found",
        )
    return record


@router.patch("/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: UUID,
    record_data: MedicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a medical record."""
    service = MedicalRecordService(db)
    record = await service.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found",
        )

    return await service.update(record, record_data, updated_by=current_user.username)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a medical record."""
    service = MedicalRecordService(db)
    record = await service.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found",
        )
    await service.delete(record)

