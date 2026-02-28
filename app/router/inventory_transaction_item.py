import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.inventory_transaction import InventoryTransactionService
from app.schema.inventory_transaction import (
    TransactionItemCreate,
    TransactionItemUpdate,
    TransactionItemResponse,
)
from app.schema.base import MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.inventory_transaction_item")

router = APIRouter(tags=["Inventory Transaction Items"])


@router.get(
    "/inventory-transactions/{transaction_id}/items",
    response_model=List[TransactionItemResponse],
)
async def get_transaction_items(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List items for a transaction."""
    logger.info("Listing items for transaction_id=%d by user_id=%d", transaction_id, current_user.id)

    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transaction not found")

    items = await service.get_items_for_transaction(transaction_id)
    return items


@router.post(
    "/inventory-transactions/{transaction_id}/items",
    response_model=TransactionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_transaction_item(
    transaction_id: int,
    data: TransactionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an item to a transaction."""
    logger.info(
        "Adding item to transaction_id=%d item_type=%s item_id=%d qty=%d by user_id=%d",
        transaction_id, data.item_type, data.item_id, data.quantity, current_user.id,
    )

    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transaction not found")

    # Validate inventory item exists
    from app.router.inventory_transaction import _validate_inventory_item
    await _validate_inventory_item(db, data.item_type, data.item_id)

    try:
        item = await service.create_item(
            transaction_id, data, transaction.transaction_type,
            created_by=current_user.username,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Build response with item name
    item_name = await service._get_item_name(item.item_type, item.item_id)
    logger.info("Transaction item created item_id=%d", item.id)
    return TransactionItemResponse(
        id=item.id,
        transaction_id=item.transaction_id,
        item_type=item.item_type,
        item_id=item.item_id,
        quantity=item.quantity,
        is_deleted=item.is_deleted,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_by=item.updated_by,
        updated_at=item.updated_at,
        item_name=item_name,
    )


@router.put(
    "/inventory-transaction-items/{item_id}",
    response_model=TransactionItemResponse,
)
async def update_transaction_item(
    item_id: int,
    data: TransactionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a transaction item."""
    logger.info("Updating transaction item_id=%d by user_id=%d", item_id, current_user.id)

    service = InventoryTransactionService(db)
    item = await service.get_item_by_id(item_id)
    if not item:
        logger.warning("Transaction item not found item_id=%d", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction item not found")

    # Validate new inventory item if changing
    update_data = data.model_dump(exclude_unset=True)
    new_item_type = update_data.get("item_type", item.item_type)
    new_item_id = update_data.get("item_id", item.item_id)
    if "item_type" in update_data or "item_id" in update_data:
        from app.router.inventory_transaction import _validate_inventory_item
        await _validate_inventory_item(db, new_item_type, new_item_id)

    try:
        updated = await service.update_item(item_id, data, updated_by=current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    item_name = await service._get_item_name(updated.item_type, updated.item_id)
    logger.info("Transaction item updated item_id=%d", item_id)
    return TransactionItemResponse(
        id=updated.id,
        transaction_id=updated.transaction_id,
        item_type=updated.item_type,
        item_id=updated.item_id,
        quantity=updated.quantity,
        is_deleted=updated.is_deleted,
        created_by=updated.created_by,
        created_at=updated.created_at,
        updated_by=updated.updated_by,
        updated_at=updated.updated_at,
        item_name=item_name,
    )


@router.delete(
    "/inventory-transaction-items/{item_id}",
    response_model=MessageResponse,
)
async def delete_transaction_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a transaction item (soft delete, reverses inventory)."""
    logger.info("Deleting transaction item_id=%d by user_id=%d", item_id, current_user.id)

    service = InventoryTransactionService(db)
    item = await service.get_item_by_id(item_id)
    if not item:
        logger.warning("Transaction item not found for deletion item_id=%d", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction item not found")

    await service.delete_item(item_id, deleted_by=current_user.username)
    logger.info("Transaction item deleted item_id=%d", item_id)
    return MessageResponse(message="Transaction item deleted successfully")
