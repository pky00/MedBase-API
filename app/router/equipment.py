import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.equipment import EquipmentService
from app.service.equipment_category import EquipmentCategoryService
from app.schema.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentDetailResponse,
)
from app.schema.enums import EquipmentCondition
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.equipment")

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.get("", response_model=PaginatedResponse[EquipmentResponse])
async def get_equipment_list(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    condition: Optional[EquipmentCondition] = Query(None, description="Filter by condition (new/good/fair/poor)"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all equipment with pagination, filtering, and sorting."""
    logger.info("Listing equipment page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = EquipmentService(db)
    items, total = await service.get_all(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        condition=condition,
        search=search,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d equipment items (total=%d)", len(items), total)

    return PaginatedResponse(
        items=items, total=total, page=page, size=size,
    )


@router.get("/{equipment_id}", response_model=EquipmentDetailResponse)
async def get_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get equipment by ID (includes inventory quantity and category name)."""
    logger.info("Fetching equipment_id=%d by user_id=%d", equipment_id, current_user.id)

    service = EquipmentService(db)
    detail = await service.get_by_id_with_details(equipment_id)

    if not detail:
        logger.warning("Equipment not found equipment_id=%d", equipment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return detail


@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    data: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create new equipment.
    
    Automatically creates an inventory record with quantity 0.
    """
    logger.info(
        "Creating equipment name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    service = EquipmentService(db)

    # Check for duplicate name
    existing = await service.get_by_name(data.name)
    if existing:
        logger.warning("Equipment name already exists name='%s'", data.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment name already exists",
        )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = EquipmentCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Equipment category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment category not found",
            )

    equipment = await service.create(data, created_by=current_user.id)

    logger.info("Equipment created equipment_id=%d", equipment.id)
    return equipment


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update equipment."""
    logger.info("Updating equipment_id=%d by user_id=%d", equipment_id, current_user.id)

    service = EquipmentService(db)

    equipment = await service.get_by_id(equipment_id)
    if not equipment:
        logger.warning("Equipment not found for update equipment_id=%d", equipment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Check for duplicate name if being updated
    if data.name and data.name != equipment.name:
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Equipment name already exists name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment name already exists",
            )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = EquipmentCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Equipment category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment category not found",
            )

    updated = await service.update(equipment_id, data, updated_by=current_user.id)
    logger.info("Equipment updated equipment_id=%d", equipment_id)
    return updated


@router.delete("/{equipment_id}", response_model=MessageResponse)
async def delete_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete equipment (soft delete). Only allowed if inventory quantity is 0."""
    logger.info("Deleting equipment_id=%d by user_id=%d", equipment_id, current_user.id)

    service = EquipmentService(db)

    equipment = await service.get_by_id(equipment_id)
    if not equipment:
        logger.warning("Equipment not found for deletion equipment_id=%d", equipment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    # Check inventory quantity
    quantity = await service.get_inventory_quantity(equipment_id)
    if quantity > 0:
        logger.warning("Cannot delete equipment with inventory quantity=%d equipment_id=%d", quantity, equipment_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete equipment with inventory quantity {quantity}. Quantity must be 0.",
        )

    await service.delete(equipment_id, deleted_by=current_user.id)
    logger.info("Equipment deleted equipment_id=%d", equipment_id)
    return MessageResponse(message="Equipment deleted successfully")
