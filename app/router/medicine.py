import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.medicine import MedicineService
from app.service.medicine_category import MedicineCategoryService
from app.schema.medicine import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse,
    MedicineDetailResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.medicine")

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.get("", response_model=PaginatedResponse[MedicineResponse])
async def get_medicines(
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
    """Get all medicines with pagination, filtering, and sorting."""
    logger.info("Listing medicines page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = MedicineService(db)
    medicines, total = await service.get_all(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        search=search,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d medicines (total=%d)", len(medicines), total)

    return PaginatedResponse(
        items=medicines, total=total, page=page, size=size,
    )


@router.get("/{medicine_id}", response_model=MedicineDetailResponse)
async def get_medicine(
    medicine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medicine by ID (includes inventory quantity and category name)."""
    logger.info("Fetching medicine_id=%d by user_id=%d", medicine_id, current_user.id)

    service = MedicineService(db)
    detail = await service.get_by_id_with_details(medicine_id)

    if not detail:
        logger.warning("Medicine not found medicine_id=%d", medicine_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    return detail


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    data: MedicineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new medicine.
    
    Automatically creates an inventory record with quantity 0.
    """
    logger.info(
        "Creating medicine name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    service = MedicineService(db)

    # Check for duplicate name
    existing = await service.get_by_name(data.name)
    if existing:
        logger.warning("Medicine name already exists name='%s'", data.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine name already exists",
        )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = MedicineCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Medicine category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine category not found",
            )

    medicine = await service.create(data, created_by=current_user.username)

    logger.info("Medicine created medicine_id=%d", medicine.id)
    return medicine


@router.put("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a medicine."""
    logger.info("Updating medicine_id=%d by user_id=%d", medicine_id, current_user.id)

    service = MedicineService(db)

    medicine = await service.get_by_id(medicine_id)
    if not medicine:
        logger.warning("Medicine not found for update medicine_id=%d", medicine_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    # Check for duplicate name if being updated
    if data.name and data.name != medicine.name:
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Medicine name already exists name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine name already exists",
            )

    # Validate category if provided
    if data.category_id is not None:
        cat_service = MedicineCategoryService(db)
        category = await cat_service.get_by_id(data.category_id)
        if not category:
            logger.warning("Medicine category not found category_id=%d", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine category not found",
            )

    updated = await service.update(medicine_id, data, updated_by=current_user.username)
    logger.info("Medicine updated medicine_id=%d", medicine_id)
    return updated


@router.delete("/{medicine_id}", response_model=MessageResponse)
async def delete_medicine(
    medicine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a medicine (soft delete). Only allowed if inventory quantity is 0."""
    logger.info("Deleting medicine_id=%d by user_id=%d", medicine_id, current_user.id)

    service = MedicineService(db)

    medicine = await service.get_by_id(medicine_id)
    if not medicine:
        logger.warning("Medicine not found for deletion medicine_id=%d", medicine_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    # Check inventory quantity
    quantity = await service.get_inventory_quantity(medicine_id)
    if quantity > 0:
        logger.warning("Cannot delete medicine with inventory quantity=%d medicine_id=%d", quantity, medicine_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete medicine with inventory quantity {quantity}. Quantity must be 0.",
        )

    await service.delete(medicine_id, deleted_by=current_user.username)
    logger.info("Medicine deleted medicine_id=%d", medicine_id)
    return MessageResponse(message="Medicine deleted successfully")
