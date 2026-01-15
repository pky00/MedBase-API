from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.vital_sign import (
    VitalSignCreate,
    VitalSignUpdate,
    VitalSignResponse,
    VitalSignListResponse,
)
from app.services.vital_sign_service import VitalSignService
from app.services.patient_service import PatientService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/patients/{patient_id}/vital-signs", tags=["vital-signs"])


@router.post("/", response_model=VitalSignResponse, status_code=status.HTTP_201_CREATED)
async def create_vital_sign(
    patient_id: UUID,
    vital_sign_data: VitalSignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record vital signs for a patient."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Override patient_id from path
    vital_sign_data.patient_id = patient_id

    service = VitalSignService(db)
    return await service.create(vital_sign_data, created_by=current_user.username)


@router.get("/", response_model=VitalSignListResponse)
async def list_vital_signs(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all vital signs for a patient."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    service = VitalSignService(db)
    vital_signs, total = await service.list_by_patient(patient_id)
    return VitalSignListResponse(data=vital_signs, total=total)


@router.get("/{vital_sign_id}", response_model=VitalSignResponse)
async def get_vital_sign(
    patient_id: UUID,
    vital_sign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific vital sign record."""
    service = VitalSignService(db)
    vital_sign = await service.get_by_id(vital_sign_id)
    if not vital_sign or vital_sign.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vital sign record not found",
        )
    return vital_sign


@router.patch("/{vital_sign_id}", response_model=VitalSignResponse)
async def update_vital_sign(
    patient_id: UUID,
    vital_sign_id: UUID,
    vital_sign_data: VitalSignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a vital sign record."""
    service = VitalSignService(db)
    vital_sign = await service.get_by_id(vital_sign_id)
    if not vital_sign or vital_sign.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vital sign record not found",
        )

    return await service.update(vital_sign, vital_sign_data, updated_by=current_user.username)


@router.delete("/{vital_sign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vital_sign(
    patient_id: UUID,
    vital_sign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a vital sign record."""
    service = VitalSignService(db)
    vital_sign = await service.get_by_id(vital_sign_id)
    if not vital_sign or vital_sign.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vital sign record not found",
        )
    await service.delete(vital_sign)

