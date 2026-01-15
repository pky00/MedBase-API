from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.equipment_category import (
    EquipmentCategoryCreate,
    EquipmentCategoryUpdate,
    EquipmentCategoryResponse,
    EquipmentCategoryListResponse,
)
from app.services.equipment_category_service import EquipmentCategoryService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/equipment-categories", tags=["equipment-categories"])


@router.post("/", response_model=EquipmentCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: EquipmentCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new equipment category."""
    service = EquipmentCategoryService(db)

    if category_data.code:
        existing = await service.get_by_code(category_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category code already exists",
            )

    return await service.create(category_data, created_by=current_user.username)


@router.get("/", response_model=EquipmentCategoryListResponse)
async def list_categories(
    is_active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all equipment categories."""
    service = EquipmentCategoryService(db)
    categories, total = await service.list_categories(is_active=is_active)
    return EquipmentCategoryListResponse(data=categories, total=total)


@router.get("/{category_id}", response_model=EquipmentCategoryResponse)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific equipment category by ID."""
    service = EquipmentCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.patch("/{category_id}", response_model=EquipmentCategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: EquipmentCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an equipment category."""
    service = EquipmentCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    if category_data.code and category_data.code != category.code:
        existing = await service.get_by_code(category_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category code already exists",
            )

    return await service.update(category, category_data, updated_by=current_user.username)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an equipment category."""
    service = EquipmentCategoryService(db)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    await service.delete(category)

