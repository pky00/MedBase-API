import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.inventory import InventoryService
from app.schema.inventory import InventoryResponse
from app.schema.base import PaginatedResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.inventory")

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryResponse])
async def get_inventory_list(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    item_type: Optional[str] = Query(None, description="Filter by item type (medicine/equipment/medical_device)"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all inventory records with pagination and filtering."""
    logger.info("Listing inventory page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = InventoryService(db)
    records, total = await service.get_all(
        page=page, size=size, item_type=item_type, sort=sort, order=order
    )

    pages = (total + size - 1) // size

    logger.info("Returning %d inventory records (total=%d)", len(records), total)

    return PaginatedResponse(
        items=records, total=total, page=page, size=size, pages=pages
    )


@router.get("/{inventory_id}", response_model=InventoryResponse)
async def get_inventory(
    inventory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inventory record by ID."""
    logger.info("Fetching inventory_id=%d by user_id=%d", inventory_id, current_user.id)

    service = InventoryService(db)
    inventory = await service.get_by_id(inventory_id)

    if not inventory:
        logger.warning("Inventory record not found inventory_id=%d", inventory_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found",
        )

    return inventory


@router.get("/item/{item_type}/{item_id}", response_model=InventoryResponse)
async def get_inventory_by_item(
    item_type: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inventory record by item type and item ID."""
    logger.info(
        "Fetching inventory for item_type='%s' item_id=%d by user_id=%d",
        item_type, item_id, current_user.id,
    )

    if item_type not in ("medicine", "equipment", "medical_device"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_type. Must be: medicine, equipment, or medical_device",
        )

    service = InventoryService(db)
    inventory = await service.get_by_item(item_type, item_id)

    if not inventory:
        logger.warning("Inventory record not found for item_type='%s' item_id=%d", item_type, item_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found",
        )

    return inventory
