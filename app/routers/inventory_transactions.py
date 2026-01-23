import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.models.enums import InventoryTransactionType, ReferenceType
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
    InventoryTransactionListResponse,
)
from app.services.inventory_transaction_service import InventoryTransactionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory-transactions", tags=["Inventory Transactions"])


@router.get("/", response_model=InventoryTransactionListResponse)
async def list_inventory_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    transaction_type: InventoryTransactionType | None = None,
    reference_type: ReferenceType | None = None,
    medicine_inventory_id: UUID | None = None,
    medical_device_inventory_id: UUID | None = None,
    equipment_id: UUID | None = None,
    sort_by: str = Query("transaction_date"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all inventory transactions with pagination and filtering."""
    service = InventoryTransactionService(db)
    transactions, total = await service.list_transactions(
        page=page,
        size=size,
        transaction_type=transaction_type,
        reference_type=reference_type,
        medicine_inventory_id=medicine_inventory_id,
        medical_device_inventory_id=medical_device_inventory_id,
        equipment_id=equipment_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return InventoryTransactionListResponse(
        data=transactions, total=total, page=page, size=size
    )


@router.get("/{transaction_id}", response_model=InventoryTransactionResponse)
async def get_inventory_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific inventory transaction by ID."""
    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transaction not found"
        )
    return transaction


@router.post("/", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_transaction(
    data: InventoryTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new inventory transaction."""
    # Validate that at least one inventory reference is provided
    if not any([data.medicine_inventory_id, data.medical_device_inventory_id, data.equipment_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of medicine_inventory_id, medical_device_inventory_id, or equipment_id must be provided"
        )
    
    service = InventoryTransactionService(db)
    transaction = await service.create(data, created_by=current_user.username)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an inventory transaction."""
    service = InventoryTransactionService(db)
    transaction = await service.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transaction not found"
        )
    await service.delete(transaction)

