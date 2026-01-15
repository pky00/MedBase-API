from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.medical_device import (
    MedicalDeviceCreate,
    MedicalDeviceUpdate,
    MedicalDeviceResponse,
    MedicalDeviceListResponse,
)
from app.services.medical_device_service import MedicalDeviceService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/medical-devices", tags=["medical-devices"])


@router.post("/", response_model=MedicalDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: MedicalDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new medical device."""
    service = MedicalDeviceService(db)

    if device_data.code:
        existing = await service.get_by_code(device_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device code already exists",
            )

    return await service.create(device_data, created_by=current_user.username)


@router.get("/", response_model=MedicalDeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all medical devices with pagination and filtering."""
    service = MedicalDeviceService(db)
    devices, total = await service.list_devices(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        search=search,
    )
    return MedicalDeviceListResponse(data=devices, total=total, page=page, size=size)


@router.get("/{device_id}", response_model=MedicalDeviceResponse)
async def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific medical device by ID."""
    service = MedicalDeviceService(db)
    device = await service.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )
    return device


@router.patch("/{device_id}", response_model=MedicalDeviceResponse)
async def update_device(
    device_id: UUID,
    device_data: MedicalDeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a medical device."""
    service = MedicalDeviceService(db)
    device = await service.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )

    if device_data.code and device_data.code != device.code:
        existing = await service.get_by_code(device_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device code already exists",
            )

    return await service.update(device, device_data, updated_by=current_user.username)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a medical device."""
    service = MedicalDeviceService(db)
    device = await service.get_by_id(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )
    await service.delete(device)

