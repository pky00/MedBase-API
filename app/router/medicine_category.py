import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.medicine_category import MedicineCategoryService
from app.schema.medicine_category import (
    MedicineCategoryCreate,
    MedicineCategoryUpdate,
    MedicineCategoryResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.medicine_category")

router = APIRouter(prefix="/medicine-categories", tags=["Medicine Categories"])


@router.get("", response_model=PaginatedResponse[MedicineCategoryResponse])
async def get_medicine_categories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all medicine categories with pagination and sorting."""
    logger.info("Listing medicine categories page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = MedicineCategoryService(db)
    categories, total = await service.get_all(
        page=page, size=size, search=search, sort=sort, order=order
    )

    logger.info("Returning %d medicine categories (total=%d)", len(categories), total)

    return PaginatedResponse(
        items=categories, total=total, page=page, size=size,
    )


@router.get("/{category_id}", response_model=MedicineCategoryResponse)
async def get_medicine_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medicine category by ID."""
    logger.info("Fetching medicine category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicineCategoryService(db)
    category = await service.get_by_id(category_id)

    if not category:
        logger.warning("Medicine category not found category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine category not found",
        )

    return category


@router.post("", response_model=MedicineCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine_category(
    data: MedicineCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new medicine category."""
    logger.info(
        "Creating medicine category name='%s' by user_id=%d",
        data.name, current_user.id,
    )

    service = MedicineCategoryService(db)

    # Check for duplicate name
    existing = await service.get_by_name(data.name)
    if existing:
        logger.warning("Medicine category name already exists name='%s'", data.name)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine category name already exists",
        )

    category = await service.create(data, created_by=current_user.username)

    logger.info("Medicine category created category_id=%d", category.id)
    return category


@router.put("/{category_id}", response_model=MedicineCategoryResponse)
async def update_medicine_category(
    category_id: int,
    data: MedicineCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a medicine category."""
    logger.info("Updating medicine category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicineCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Medicine category not found for update category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine category not found",
        )

    # Check for duplicate name if being updated
    if data.name and data.name != category.name:
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Medicine category name already exists name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine category name already exists",
            )

    updated = await service.update(category_id, data, updated_by=current_user.username)
    logger.info("Medicine category updated category_id=%d", category_id)
    return updated


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_medicine_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a medicine category (soft delete). Cannot delete if medicines are linked."""
    logger.info("Deleting medicine category_id=%d by user_id=%d", category_id, current_user.id)

    service = MedicineCategoryService(db)

    category = await service.get_by_id(category_id)
    if not category:
        logger.warning("Medicine category not found for deletion category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine category not found",
        )

    # Check for linked medicines
    if await service.has_linked_medicines(category_id):
        logger.warning("Cannot delete medicine category with linked medicines category_id=%d", category_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with linked medicines",
        )

    await service.delete(category_id, deleted_by=current_user.username)
    logger.info("Medicine category deleted category_id=%d", category_id)
    return MessageResponse(message="Medicine category deleted successfully")
