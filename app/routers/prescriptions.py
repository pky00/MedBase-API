from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.enums import PrescriptionStatus
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
    PrescriptionListResponse,
)
from app.services.prescription_service import PrescriptionService
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new prescription."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(prescription_data.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not found",
        )

    # Validate doctor exists
    doctor_service = DoctorService(db)
    doctor = await doctor_service.get_by_id(prescription_data.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor not found",
        )

    service = PrescriptionService(db)
    return await service.create(prescription_data, created_by=current_user.username)


@router.get("/", response_model=PrescriptionListResponse)
async def list_prescriptions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    patient_id: UUID | None = None,
    doctor_id: UUID | None = None,
    status: PrescriptionStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all prescriptions with pagination and filtering."""
    service = PrescriptionService(db)
    prescriptions, total = await service.list_prescriptions(
        page=page,
        size=size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return PrescriptionListResponse(data=prescriptions, total=total, page=page, size=size)


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific prescription by ID."""
    service = PrescriptionService(db)
    prescription = await service.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )
    return prescription


@router.patch("/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: UUID,
    prescription_data: PrescriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a prescription."""
    service = PrescriptionService(db)
    prescription = await service.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    return await service.update(prescription, prescription_data, updated_by=current_user.username)


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription(
    prescription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a prescription."""
    service = PrescriptionService(db)
    prescription = await service.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )
    await service.delete(prescription)

