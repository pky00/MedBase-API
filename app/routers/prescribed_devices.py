from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.prescribed_device import (
    PrescribedDeviceCreate,
    PrescribedDeviceUpdate,
    PrescribedDeviceResponse,
    PrescribedDeviceListResponse,
)
from app.services.prescribed_device_service import PrescribedDeviceService
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.services.medical_device_service import MedicalDeviceService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/prescribed-devices", tags=["prescribed-devices"])


@router.post("/", response_model=PrescribedDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_prescribed_device(
    device_data: PrescribedDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Prescribe a medical device to a patient."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(device_data.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not found",
        )

    # Validate doctor exists
    doctor_service = DoctorService(db)
    doctor = await doctor_service.get_by_id(device_data.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor not found",
        )

    # Validate device exists
    device_service = MedicalDeviceService(db)
    device = await device_service.get_by_id(device_data.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical device not found",
        )

    service = PrescribedDeviceService(db)
    return await service.create(device_data, created_by=current_user.username)


@router.get("/", response_model=PrescribedDeviceListResponse)
async def list_prescribed_devices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    patient_id: UUID | None = None,
    doctor_id: UUID | None = None,
    device_id: UUID | None = None,
    is_returned: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all prescribed devices with pagination and filtering."""
    service = PrescribedDeviceService(db)
    devices, total = await service.list_prescribed_devices(
        page=page,
        size=size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        device_id=device_id,
        is_returned=is_returned,
    )
    return PrescribedDeviceListResponse(data=devices, total=total, page=page, size=size)


@router.get("/{prescribed_device_id}", response_model=PrescribedDeviceResponse)
async def get_prescribed_device(
    prescribed_device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific prescribed device by ID."""
    service = PrescribedDeviceService(db)
    device = await service.get_by_id(prescribed_device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescribed device not found",
        )
    return device


@router.patch("/{prescribed_device_id}", response_model=PrescribedDeviceResponse)
async def update_prescribed_device(
    prescribed_device_id: UUID,
    device_data: PrescribedDeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a prescribed device (e.g., record return)."""
    service = PrescribedDeviceService(db)
    device = await service.get_by_id(prescribed_device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescribed device not found",
        )

    return await service.update(device, device_data, updated_by=current_user.username)


@router.delete("/{prescribed_device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescribed_device(
    prescribed_device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a prescribed device."""
    service = PrescribedDeviceService(db)
    device = await service.get_by_id(prescribed_device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescribed device not found",
        )
    await service.delete(device)

