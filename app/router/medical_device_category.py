import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.medical_device_category import MedicalDeviceCategoryService
from app.schema.medical_device_category import (
    MedicalDeviceCategoryCreate,
    MedicalDeviceCategoryUpdate,
    MedicalDeviceCategoryResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.medical_device_category")

router = APIRouter(prefix="/medical-device-categories", tags=["Medical Device Categories"])


@router.get("", response_model=PaginatedResponse[MedicalDeviceCategoryResponse])
async def get_medical_device_categories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all medical device categories with pagination and sorting."""
    logger.info("Listing medical device categories page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = MedicalDeviceCategoryService(db)
    categories, total = await service.get_all(
        page=page, size=size, search=search, sort=sort, order=order
    )

    pages = (total + size - 1) // size

    logger.info("Returning %d medical device categories (total=%d)", len(categories), total)

    return PaginatedResponse(
        items=categories, total=total, page=page, size=size, pages=pages
    )


@router.get("/{category_id}", response_model=MedicalDeviceCategoryResponse)
async def get_medical_device_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medical device category by ID."""
    logger.info("Fetching medical device category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicalDeviceCategoryService(db)
    category = await service.get_by_id(category_id)

    if not category:
        logger.warning("Medical device category not found category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device category not found",
        )

    return category


@router.post("", response_model=MedicalDeviceCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_device_category(
    data: MedicalDeviceCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new medical device category."""
    logger.info(
        "Creating medical device category name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    service = MedicalDeviceCategoryService(db)
    category = await service.create(data, created_by=current_user.id)

    logger.info("Medical device category created category_id=%d", category.id)
    return category


@router.put("/{category_id}", response_model=MedicalDeviceCategoryResponse)
async def update_medical_device_category(
    category_id: int,
    data: MedicalDeviceCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a medical device category."""
    logger.info("Updating medical device category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicalDeviceCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Medical device category not found for update category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device category not found",
        )

    updated = await service.update(category_id, data, updated_by=current_user.id)
    logger.info("Medical device category updated category_id=%d", category_id)
    return updated


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_medical_device_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a medical device category (soft delete). Cannot delete if medical devices are linked."""
    logger.info("Deleting medical device category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicalDeviceCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Medical device category not found for deletion category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device category not found",
        )

    # Check for linked medical devices
    if await service.has_linked_devices(category_id):
        logger.warning("Cannot delete medical device category with linked devices category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with linked medical devices",
        )

    await service.delete(category_id, deleted_by=current_user.id)
    logger.info("Medical device category deleted category_id=%d", category_id)
    return MessageResponse(message="Medical device category deleted successfully")
