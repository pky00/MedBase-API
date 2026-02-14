import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.medical_device import MedicalDeviceService
from app.service.medical_device_category import MedicalDeviceCategoryService
from app.schema.medical_device import (
    MedicalDeviceCreate,
    MedicalDeviceUpdate,
    MedicalDeviceResponse,
    MedicalDeviceDetailResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.medical_device")

router = APIRouter(prefix="/medical-devices", tags=["Medical Devices"])


@router.get("", response_model=PaginatedResponse[MedicalDeviceResponse])
async def get_medical_devices(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all medical devices with pagination, filtering, and sorting."""
    logger.info("Listing medical devices page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = MedicalDeviceService(db)
    devices, total = await service.get_all(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        search=search,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d medical devices (total=%d)", len(devices), total)

    return PaginatedResponse(
        items=devices, total=total, page=page, size=size,
    )


@router.get("/{device_id}", response_model=MedicalDeviceDetailResponse)
async def get_medical_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medical device by ID (includes inventory quantity and category name)."""
    logger.info("Fetching medical device_id=%d by user_id=%d", device_id, current_user.id)

    service = MedicalDeviceService(db)
    detail = await service.get_by_id_with_details(device_id)

    if not detail:
        logger.warning("Medical device not found device_id=%d", device_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )

    return detail


@router.post("", response_model=MedicalDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_device(
    data: MedicalDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new medical device.
    
    Automatically creates an inventory record with quantity 0.
    """
    logger.info(
        "Creating medical device name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = MedicalDeviceCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Medical device category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medical device category not found",
            )

    service = MedicalDeviceService(db)
    device = await service.create(data, created_by=current_user.id)

    logger.info("Medical device created device_id=%d", device.id)
    return device


@router.put("/{device_id}", response_model=MedicalDeviceResponse)
async def update_medical_device(
    device_id: int,
    data: MedicalDeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a medical device."""
    logger.info("Updating medical device_id=%d by user_id=%d", device_id, current_user.id)

    service = MedicalDeviceService(db)

    device = await service.get_by_id(device_id)
    if not device:
        logger.warning("Medical device not found for update device_id=%d", device_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = MedicalDeviceCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Medical device category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medical device category not found",
            )

    updated = await service.update(device_id, data, updated_by=current_user.id)
    logger.info("Medical device updated device_id=%d", device_id)
    return updated


@router.delete("/{device_id}", response_model=MessageResponse)
async def delete_medical_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a medical device (soft delete). Only allowed if inventory quantity is 0."""
    logger.info("Deleting medical device_id=%d by user_id=%d", device_id, current_user.id)

    service = MedicalDeviceService(db)

    device = await service.get_by_id(device_id)
    if not device:
        logger.warning("Medical device not found for deletion device_id=%d", device_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device not found",
        )

    # Check inventory quantity
    quantity = await service.get_inventory_quantity(device_id)
    if quantity > 0:
        logger.warning("Cannot delete medical device with inventory quantity=%d device_id=%d", quantity, device_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete medical device with inventory quantity {quantity}. Quantity must be 0.",
        )

    await service.delete(device_id, deleted_by=current_user.id)
    logger.info("Medical device deleted device_id=%d", device_id)
    return MessageResponse(message="Medical device deleted successfully")
