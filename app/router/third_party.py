import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.third_party import ThirdPartyService
from app.schema.third_party import ThirdPartyResponse, ThirdPartyType
from app.schema.base import PaginatedResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.third_party")

router = APIRouter(prefix="/third-parties", tags=["Third Parties"])


@router.get("", response_model=PaginatedResponse[ThirdPartyResponse])
async def get_third_parties(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    type: Optional[ThirdPartyType] = Query(None, description="Filter by type (user/doctor/patient/partner)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, email, phone"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all third parties with pagination and filtering. Read-only."""
    logger.info("Listing third parties page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = ThirdPartyService(db)
    records, total = await service.get_all(
        page=page, size=size, type=type, is_active=is_active,
        search=search, sort=sort, order=order,
    )

    logger.info("Returning %d third parties (total=%d)", len(records), total)
    return PaginatedResponse(items=records, total=total, page=page, size=size)


@router.get("/{third_party_id}", response_model=ThirdPartyResponse)
async def get_third_party(
    third_party_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get third party by ID."""
    logger.info("Fetching third_party_id=%d by user_id=%d", third_party_id, current_user.id)

    service = ThirdPartyService(db)
    record = await service.get_by_id(third_party_id)

    if not record:
        logger.warning("Third party not found third_party_id=%d", third_party_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Third party not found",
        )

    return record
