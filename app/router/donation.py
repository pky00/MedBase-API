import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.donation import DonationService
from app.service.partner import PartnerService
from app.schema.donation import (
    DonationCreate,
    DonationUpdate,
    DonationResponse,
    DonationDetailResponse,
    DonationItemCreate,
    DonationItemUpdate,
    DonationItemResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.donation")

router = APIRouter(tags=["Donations"])


# --- Donation endpoints ---

@router.get("/donations", response_model=PaginatedResponse[DonationResponse])
async def get_donations(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    partner_id: Optional[int] = Query(None, description="Filter by partner ID"),
    donation_date: Optional[date] = Query(None, description="Filter by donation date"),
    search: Optional[str] = Query(None, description="Search in notes and partner name"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all donations with pagination, filtering, and sorting."""
    logger.info("Listing donations page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = DonationService(db)
    donations, total = await service.get_all(
        page=page,
        size=size,
        partner_id=partner_id,
        donation_date=str(donation_date) if donation_date else None,
        search=search,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d donations (total=%d)", len(donations), total)

    return PaginatedResponse(
        items=donations, total=total, page=page, size=size,
    )


@router.get("/donations/{donation_id}", response_model=DonationDetailResponse)
async def get_donation(
    donation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get donation by ID (includes items)."""
    logger.info("Fetching donation_id=%d by user_id=%d", donation_id, current_user.id)

    service = DonationService(db)
    detail = await service.get_by_id_with_details(donation_id)

    if not detail:
        logger.warning("Donation not found donation_id=%d", donation_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    return detail


@router.post("/donations", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    data: DonationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new donation with optional items. Creates inventory transactions automatically."""
    logger.info(
        "Creating donation partner_id=%d by user_id=%d",
        data.partner_id, current_user.id,
    )

    # Validate partner exists
    partner_service = PartnerService(db)
    partner = await partner_service.get_by_id(data.partner_id)
    if not partner:
        logger.warning("Partner not found partner_id=%d", data.partner_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner not found",
        )

    # Validate items if provided
    donation_service = DonationService(db)
    if data.items:
        for item in data.items:
            exists = await donation_service.validate_item_exists(item.item_type, item.item_id)
            if not exists:
                logger.warning(
                    "Item not found item_type='%s' item_id=%d", item.item_type, item.item_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item not found: {item.item_type} with id {item.item_id}",
                )

    donation = await donation_service.create(data, created_by=current_user.id)

    logger.info("Donation created donation_id=%d", donation.id)
    return DonationResponse(
        id=donation.id,
        partner_id=donation.partner_id,
        donation_date=donation.donation_date,
        notes=donation.notes,
        is_deleted=donation.is_deleted,
        created_by=donation.created_by,
        created_at=donation.created_at,
        updated_by=donation.updated_by,
        updated_at=donation.updated_at,
        partner_name=partner.name,
    )


@router.put("/donations/{donation_id}", response_model=DonationResponse)
async def update_donation(
    donation_id: int,
    data: DonationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a donation."""
    logger.info("Updating donation_id=%d by user_id=%d", donation_id, current_user.id)

    service = DonationService(db)

    donation = await service.get_by_id(donation_id)
    if not donation:
        logger.warning("Donation not found for update donation_id=%d", donation_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    # Validate partner if being changed
    if data.partner_id is not None:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            logger.warning("Partner not found partner_id=%d", data.partner_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner not found",
            )

    updated = await service.update(donation_id, data, updated_by=current_user.id)
    logger.info("Donation updated donation_id=%d", donation_id)

    # Get partner name for response
    partner_service = PartnerService(db)
    partner = await partner_service.get_by_id(updated.partner_id)

    return DonationResponse(
        id=updated.id,
        partner_id=updated.partner_id,
        donation_date=updated.donation_date,
        notes=updated.notes,
        is_deleted=updated.is_deleted,
        created_by=updated.created_by,
        created_at=updated.created_at,
        updated_by=updated.updated_by,
        updated_at=updated.updated_at,
        partner_name=partner.name if partner else None,
    )


@router.delete("/donations/{donation_id}", response_model=MessageResponse)
async def delete_donation(
    donation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a donation (soft delete). Reverses inventory changes."""
    logger.info("Deleting donation_id=%d by user_id=%d", donation_id, current_user.id)

    service = DonationService(db)

    donation = await service.get_by_id(donation_id)
    if not donation:
        logger.warning("Donation not found for deletion donation_id=%d", donation_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    await service.delete(donation_id, deleted_by=current_user.id)
    logger.info("Donation deleted donation_id=%d", donation_id)
    return MessageResponse(message="Donation deleted successfully")


# --- Donation Items endpoints ---

@router.get("/donations/{donation_id}/items", response_model=list[DonationItemResponse])
async def get_donation_items(
    donation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all items for a donation."""
    logger.info("Listing items for donation_id=%d by user_id=%d", donation_id, current_user.id)

    donation_service = DonationService(db)

    # Verify donation exists
    donation = await donation_service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    items = await donation_service.get_items_for_donation(donation_id)
    return items


@router.post("/donations/{donation_id}/items", response_model=DonationItemResponse, status_code=status.HTTP_201_CREATED)
async def add_donation_item(
    donation_id: int,
    data: DonationItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an item to a donation. Updates inventory automatically."""
    logger.info(
        "Adding item to donation_id=%d item_type='%s' item_id=%d by user_id=%d",
        donation_id, data.item_type, data.item_id, current_user.id,
    )

    donation_service = DonationService(db)

    # Verify donation exists
    donation = await donation_service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    # Validate item exists
    exists = await donation_service.validate_item_exists(data.item_type, data.item_id)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item not found: {data.item_type} with id {data.item_id}",
        )

    item = await donation_service.add_item_to_donation(
        donation_id=donation_id,
        data=data,
        created_by=current_user.id,
    )

    # Resolve item name for response
    item_name = await donation_service._resolve_item_name(item.item_type, item.item_id)

    return DonationItemResponse(
        id=item.id,
        donation_id=item.donation_id,
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


@router.put("/donation-items/{item_id}", response_model=DonationItemResponse)
async def update_donation_item(
    item_id: int,
    data: DonationItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a donation item. Adjusts inventory automatically."""
    logger.info("Updating donation item_id=%d by user_id=%d", item_id, current_user.id)

    donation_service = DonationService(db)

    item = await donation_service.get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation item not found",
        )

    # Validate new item reference if being changed
    update_data = data.model_dump(exclude_unset=True)
    check_item_type = update_data.get("item_type", item.item_type)
    check_item_id = update_data.get("item_id", item.item_id)
    if "item_type" in update_data or "item_id" in update_data:
        exists = await donation_service.validate_item_exists(check_item_type, check_item_id)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item not found: {check_item_type} with id {check_item_id}",
            )

    updated = await donation_service.update_item(item_id, data, updated_by=current_user.id)

    # Resolve item name for response
    item_name = await donation_service._resolve_item_name(updated.item_type, updated.item_id)

    return DonationItemResponse(
        id=updated.id,
        donation_id=updated.donation_id,
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


@router.delete("/donation-items/{item_id}", response_model=MessageResponse)
async def delete_donation_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a donation item (soft delete). Reverses inventory change."""
    logger.info("Deleting donation item_id=%d by user_id=%d", item_id, current_user.id)

    donation_service = DonationService(db)

    item = await donation_service.get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation item not found",
        )

    await donation_service.delete_item(item_id, deleted_by=current_user.id)
    logger.info("Donation item deleted item_id=%d", item_id)
    return MessageResponse(message="Donation item deleted successfully")
