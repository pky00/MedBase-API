import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.inventory_transaction import InventoryTransactionService
from app.schema.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
    TransactionType,
)
from app.schema.inventory import ItemType
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.inventory_transaction")

router = APIRouter(prefix="/inventory-transactions", tags=["Inventory Transactions"])


@router.get("", response_model=PaginatedResponse[InventoryTransactionResponse])
async def get_inventory_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all inventory transactions with pagination and filtering."""
    logger.info("Listing inventory transactions page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = InventoryTransactionService(db)
    transactions, total = await service.get_all(
        page=page,
        size=size,
        transaction_type=transaction_type,
        item_type=item_type,
        item_id=item_id,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d inventory transactions (total=%d)", len(transactions), total)

    return PaginatedResponse(
        items=transactions, total=total, page=page, size=size,
    )


@router.get("/{transaction_id}", response_model=InventoryTransactionResponse)
async def get_inventory_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inventory transaction by ID."""
    logger.info("Fetching transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)

    if not transaction:
        logger.warning("Inventory transaction not found transaction_id=%d", transaction_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transaction not found",
        )

    return transaction


@router.post("", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_transaction(
    data: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an inventory transaction. Automatically updates inventory quantity.

    + for purchase/donation, - for prescription/loss/breakage/expiration/destruction.
    """
    logger.info(
        "Creating inventory transaction type='%s' item_type='%s' item_id=%d qty=%d by user_id=%d",
        data.transaction_type, data.item_type, data.item_id, data.quantity, current_user.id,
    )

    service = InventoryTransactionService(db)

    # Validate item exists
    exists = await service.validate_item_exists(data.item_type, data.item_id)
    if not exists:
        logger.warning("Item not found item_type='%s' item_id=%d", data.item_type, data.item_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item not found: {data.item_type} with id {data.item_id}",
        )

    transaction = await service.create(data, created_by=current_user.id)

    logger.info("Inventory transaction created transaction_id=%d", transaction.id)
    return transaction


@router.delete("/{transaction_id}", response_model=MessageResponse)
async def delete_inventory_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an inventory transaction (soft delete). Reverses the inventory change."""
    logger.info("Deleting transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)

    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        logger.warning("Inventory transaction not found for deletion transaction_id=%d", transaction_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transaction not found",
        )

    await service.delete(transaction_id, deleted_by=current_user.id)
    logger.info("Inventory transaction deleted transaction_id=%d", transaction_id)
    return MessageResponse(message="Inventory transaction deleted successfully")
