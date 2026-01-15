from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.prescription_item import (
    PrescriptionItemCreate,
    PrescriptionItemUpdate,
    PrescriptionItemResponse,
    PrescriptionItemListResponse,
)
from app.services.prescription_item_service import PrescriptionItemService
from app.services.prescription_service import PrescriptionService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/prescriptions/{prescription_id}/items", tags=["prescription-items"])


@router.post("/", response_model=PrescriptionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription_item(
    prescription_id: UUID,
    item_data: PrescriptionItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an item to a prescription."""
    # Validate prescription exists
    prescription_service = PrescriptionService(db)
    prescription = await prescription_service.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    # Override prescription_id from path
    item_data.prescription_id = prescription_id

    service = PrescriptionItemService(db)
    return await service.create(item_data, created_by=current_user.username)


@router.get("/", response_model=PrescriptionItemListResponse)
async def list_prescription_items(
    prescription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all items for a prescription."""
    # Validate prescription exists
    prescription_service = PrescriptionService(db)
    prescription = await prescription_service.get_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    service = PrescriptionItemService(db)
    items, total = await service.list_by_prescription(prescription_id)
    return PrescriptionItemListResponse(data=items, total=total)


@router.get("/{item_id}", response_model=PrescriptionItemResponse)
async def get_prescription_item(
    prescription_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific prescription item."""
    service = PrescriptionItemService(db)
    item = await service.get_by_id(item_id)
    if not item or item.prescription_id != prescription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription item not found",
        )
    return item


@router.patch("/{item_id}", response_model=PrescriptionItemResponse)
async def update_prescription_item(
    prescription_id: UUID,
    item_id: UUID,
    item_data: PrescriptionItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a prescription item."""
    service = PrescriptionItemService(db)
    item = await service.get_by_id(item_id)
    if not item or item.prescription_id != prescription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription item not found",
        )

    return await service.update(item, item_data, updated_by=current_user.username)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prescription_item(
    prescription_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a prescription item."""
    service = PrescriptionItemService(db)
    item = await service.get_by_id(item_id)
    if not item or item.prescription_id != prescription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription item not found",
        )
    await service.delete(item)

