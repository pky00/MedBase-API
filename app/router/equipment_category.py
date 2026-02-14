import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.equipment_category import EquipmentCategoryService
from app.schema.equipment_category import (
    EquipmentCategoryCreate,
    EquipmentCategoryUpdate,
    EquipmentCategoryResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.equipment_category")

router = APIRouter(prefix="/equipment-categories", tags=["Equipment Categories"])


@router.get("", response_model=PaginatedResponse[EquipmentCategoryResponse])
async def get_equipment_categories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all equipment categories with pagination and sorting."""
    logger.info("Listing equipment categories page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = EquipmentCategoryService(db)
    categories, total = await service.get_all(
        page=page, size=size, search=search, sort=sort, order=order
    )

    logger.info("Returning %d equipment categories (total=%d)", len(categories), total)

    return PaginatedResponse(
        items=categories, total=total, page=page, size=size,
    )


@router.get("/{category_id}", response_model=EquipmentCategoryResponse)
async def get_equipment_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get equipment category by ID."""
    logger.info("Fetching equipment category_id=%d by user_id=%d", category_id, current_user.id)

    service = EquipmentCategoryService(db)
    category = await service.get_by_id(category_id)

    if not category:
        logger.warning("Equipment category not found category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment category not found",
        )

    return category


@router.post("", response_model=EquipmentCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment_category(
    data: EquipmentCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new equipment category."""
    logger.info(
        "Creating equipment category name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    service = EquipmentCategoryService(db)

    # Check for duplicate name
    existing = await service.get_by_name(data.name)
    if existing:
        logger.warning("Equipment category name already exists name='%s'", data.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment category name already exists",
        )

    category = await service.create(data, created_by=current_user.id)

    logger.info("Equipment category created category_id=%d", category.id)
    return category


@router.put("/{category_id}", response_model=EquipmentCategoryResponse)
async def update_equipment_category(
    category_id: int,
    data: EquipmentCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an equipment category."""
    logger.info("Updating equipment category_id=%d by user_id=%d", category_id, current_user.id)

    service = EquipmentCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Equipment category not found for update category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment category not found",
        )

    # Check for duplicate name if being updated
    if data.name and data.name != category.name:
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Equipment category name already exists name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment category name already exists",
            )

    updated = await service.update(category_id, data, updated_by=current_user.id)
    logger.info("Equipment category updated category_id=%d", category_id)
    return updated


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_equipment_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an equipment category (soft delete). Cannot delete if equipment items are linked."""
    logger.info("Deleting equipment category_id=%d by user_id=%d", category_id, current_user.id)

    service = EquipmentCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Equipment category not found for deletion category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment category not found",
        )

    # Check for linked equipment
    if await service.has_linked_equipment(category_id):
        logger.warning("Cannot delete equipment category with linked equipment category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with linked equipment",
        )

    await service.delete(category_id, deleted_by=current_user.id)
    logger.info("Equipment category deleted category_id=%d", category_id)
    return MessageResponse(message="Equipment category deleted successfully")
