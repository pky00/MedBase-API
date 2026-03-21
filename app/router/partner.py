import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.partner import PartnerService
from app.service.third_party import ThirdPartyService
from app.schema.partner import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse,
    PartnerType,
    OrganizationType,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.partner")

router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("", response_model=PaginatedResponse[PartnerResponse])
async def get_partners(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    partner_type: Optional[PartnerType] = Query(None, description="Filter by partner type"),
    organization_type: Optional[OrganizationType] = Query(None, description="Filter by organization type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, contact_person, email, phone"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all partners with pagination, filtering, and sorting.

    Returns a paginated list of partners with their third party details (name, phone, email).

    **Filters:**
    - **partner_type**: `donor`, `referral`, `both`
    - **organization_type**: `NGO`, `organization`, `individual`, `hospital`, `medical_center`
    - **is_active**: `true` / `false`

    **Search:** Searches in name, contact person, email, and phone.

    **Sorting:** Default `id asc`. Sortable fields validated server-side.

    **Errors:**
    - `401`: Not authenticated
    """
    logger.info("Listing partners page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = PartnerService(db)
    partners, total = await service.get_all(
        page=page, size=size, partner_type=partner_type,
        organization_type=organization_type, is_active=is_active,
        search=search, sort=sort, order=order,
    )

    logger.info("Returning %d partners (total=%d)", len(partners), total)
    return PaginatedResponse(items=partners, total=total, page=page, size=size)


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single partner by ID.

    Returns partner info including third party details (name, phone, email).

    **Errors:**
    - `401`: Not authenticated
    - `404`: Partner not found
    """
    logger.info("Fetching partner_id=%d by user_id=%d", partner_id, current_user.id)

    service = PartnerService(db)
    partner = await service.get_by_id(partner_id)

    if not partner:
        logger.warning("Partner not found partner_id=%d", partner_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    return partner


@router.post("", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    data: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new partner.

    If `third_party_id` is provided, links to an existing third party record.
    Otherwise, a new third party is auto-created using the provided `name`, `phone`, and `email`.

    **Business Rules:**
    - Name must be unique across all third parties (when creating new)
    - `name` is required when `third_party_id` is not provided

    **Partner types determine capabilities:**
    - `donor`: Can make donation inventory transactions
    - `referral`: Can receive treatments
    - `both`: Can do both

    **Errors:**
    - `400`: Name already exists, name required, or third party not found
    - `401`: Not authenticated
    """
    logger.info("Creating partner name='%s' by user_id=%d", data.name, current_user.id)

    service = PartnerService(db)

    # Validate third_party_id if provided, otherwise check name uniqueness
    if data.third_party_id:
        tp_service = ThirdPartyService(db)
        tp = await tp_service.get_by_id(data.third_party_id)
        if not tp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Third party not found")
    else:
        if not data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name is required when not providing a third_party_id",
            )
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Third party name already exists name='%s'", data.name)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Third party name already exists")
        tp_service = ThirdPartyService(db)
        existing_tp = await tp_service.get_by_name(data.name)
        if existing_tp:
            logger.warning("Name already exists in third parties name='%s'", data.name)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name already exists in third parties")

    partner = await service.create(data, created_by=current_user.username)
    logger.info("Partner created partner_id=%d", partner.id)
    return partner


@router.put("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: int,
    data: PartnerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing partner.

    All fields are optional — only provided fields are updated.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Partner not found
    """
    logger.info("Updating partner_id=%d by user_id=%d", partner_id, current_user.id)

    service = PartnerService(db)

    partner = await service.get_by_id(partner_id)
    if not partner:
        logger.warning("Partner not found for update partner_id=%d", partner_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    updated = await service.update(partner_id, data, updated_by=current_user.username)
    logger.info("Partner updated partner_id=%d", partner_id)
    return updated


@router.delete("/{partner_id}", response_model=MessageResponse)
async def delete_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a partner.

    The partner record is marked as deleted but remains in the database.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Partner not found
    """
    logger.info("Deleting partner_id=%d by user_id=%d", partner_id, current_user.id)

    service = PartnerService(db)

    partner = await service.get_by_id(partner_id)
    if not partner:
        logger.warning("Partner not found for deletion partner_id=%d", partner_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    await service.delete(partner_id, deleted_by=current_user.username)
    logger.info("Partner deleted partner_id=%d", partner_id)
    return MessageResponse(message="Partner deleted successfully")
