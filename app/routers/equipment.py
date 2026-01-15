from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
)
from app.services.equipment_service import EquipmentService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new equipment."""
    service = EquipmentService(db)

    if equipment_data.asset_code:
        existing = await service.get_by_asset_code(equipment_data.asset_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset code already exists",
            )

    if equipment_data.serial_number:
        existing = await service.get_by_serial_number(equipment_data.serial_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Serial number already registered",
            )

    return await service.create(equipment_data, created_by=current_user.username)


@router.get("/", response_model=EquipmentListResponse)
async def list_equipment(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: UUID | None = None,
    is_active: bool | None = None,
    is_donation: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all equipment with pagination and filtering."""
    service = EquipmentService(db)
    equipment, total = await service.list_equipment(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        is_donation=is_donation,
        search=search,
    )
    return EquipmentListResponse(data=equipment, total=total, page=page, size=size)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific equipment by ID."""
    service = EquipmentService(db)
    equipment = await service.get_by_id(equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )
    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: UUID,
    equipment_data: EquipmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update equipment."""
    service = EquipmentService(db)
    equipment = await service.get_by_id(equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    if equipment_data.asset_code and equipment_data.asset_code != equipment.asset_code:
        existing = await service.get_by_asset_code(equipment_data.asset_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset code already exists",
            )

    if equipment_data.serial_number and equipment_data.serial_number != equipment.serial_number:
        existing = await service.get_by_serial_number(equipment_data.serial_number)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Serial number already registered",
            )

    return await service.update(equipment, equipment_data, updated_by=current_user.username)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete equipment."""
    service = EquipmentService(db)
    equipment = await service.get_by_id(equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )
    await service.delete(equipment)

