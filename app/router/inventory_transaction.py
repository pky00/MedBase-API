import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.inventory_transaction import InventoryTransactionService
from app.schema.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionUpdate,
    InventoryTransactionResponse,
    InventoryTransactionListResponse,
    TransactionType,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.inventory_transaction")

router = APIRouter(prefix="/inventory-transactions", tags=["Inventory Transactions"])

# Types where third_party_id is auto-set to the current user's third_party
AUTO_THIRD_PARTY_TYPES = {"purchase", "loss", "breakage", "expiration", "destruction"}


@router.get("", response_model=PaginatedResponse[InventoryTransactionListResponse])
async def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    third_party_id: Optional[int] = Query(None, description="Filter by third party"),
    transaction_date: Optional[date] = Query(None, description="Filter by date"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all inventory transactions."""
    logger.info("Listing inventory transactions page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = InventoryTransactionService(db)
    transactions, total = await service.get_all(
        page=page, size=size, transaction_type=transaction_type,
        third_party_id=third_party_id, transaction_date=str(transaction_date) if transaction_date else None,
        sort=sort, order=order,
    )

    logger.info("Returning %d inventory transactions (total=%d)", len(transactions), total)
    return PaginatedResponse(items=transactions, total=total, page=page, size=size)


@router.get("/{transaction_id}", response_model=InventoryTransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get inventory transaction by ID (includes items)."""
    logger.info("Fetching inventory transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)
    result = await service.get_by_id_with_items(transaction_id)
    if not result:
        logger.warning("Inventory transaction not found transaction_id=%d", transaction_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transaction not found")

    return result


@router.post("", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: InventoryTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an inventory transaction with optional items."""
    logger.info(
        "Creating inventory transaction type=%s by user_id=%d",
        data.transaction_type, current_user.id,
    )

    service = InventoryTransactionService(db)

    # Determine third_party_id based on transaction type
    if data.transaction_type in AUTO_THIRD_PARTY_TYPES:
        third_party_id = current_user.third_party_id
    elif data.transaction_type == "donation":
        if not data.third_party_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="third_party_id is required for donation transactions",
            )
        try:
            await service.validate_donation_third_party(data.third_party_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        third_party_id = data.third_party_id
    elif data.transaction_type == "prescription":
        if not data.third_party_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="third_party_id is required for prescription transactions",
            )
        try:
            await service.validate_prescription_third_party(data.third_party_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        third_party_id = data.third_party_id
    else:
        third_party_id = current_user.third_party_id

    # Validate items if provided
    if data.items:
        for item in data.items:
            try:
                await service.validate_inventory_item(item.item_type, item.item_id)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        transaction = await service.create(data, third_party_id, created_by=current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    logger.info("Inventory transaction created id=%d", transaction.id)

    result = await service.get_by_id_with_items(transaction.id)
    return result


@router.put("/{transaction_id}", response_model=InventoryTransactionResponse)
async def update_transaction(
    transaction_id: int,
    data: InventoryTransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an inventory transaction (date and notes only)."""
    logger.info("Updating inventory transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        logger.warning("Inventory transaction not found for update transaction_id=%d", transaction_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transaction not found")

    await service.update(transaction_id, data, updated_by=current_user.username)
    logger.info("Inventory transaction updated transaction_id=%d", transaction_id)

    result = await service.get_by_id_with_items(transaction_id)
    return result


@router.delete("/{transaction_id}", response_model=MessageResponse)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an inventory transaction (soft delete, reverses inventory)."""
    logger.info("Deleting inventory transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        logger.warning("Inventory transaction not found for deletion transaction_id=%d", transaction_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transaction not found")

    await service.delete(transaction_id, deleted_by=current_user.username)
    logger.info("Inventory transaction deleted transaction_id=%d", transaction_id)
    return MessageResponse(message="Inventory transaction deleted successfully")
