from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.donor import (
    DonorCreate,
    DonorUpdate,
    DonorResponse,
    DonorListResponse,
)
from app.services.donor_service import DonorService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/donors", tags=["donors"])


@router.post("/", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    donor_data: DonorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new donor."""
    donor_service = DonorService(db)

    if donor_data.donor_code:
        existing = await donor_service.get_by_code(donor_data.donor_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Donor code already exists",
            )

    if donor_data.email:
        existing = await donor_service.get_by_email(donor_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    return await donor_service.create(donor_data, created_by=current_user.username)


@router.get("/", response_model=DonorListResponse)
async def list_donors(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    donor_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all donors with pagination and filtering."""
    donor_service = DonorService(db)
    donors, total = await donor_service.list_donors(
        page=page,
        size=size,
        donor_type=donor_type,
        is_active=is_active,
        search=search,
    )
    return DonorListResponse(data=donors, total=total, page=page, size=size)


@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(
    donor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific donor by ID."""
    donor_service = DonorService(db)
    donor = await donor_service.get_by_id(donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )
    return donor


@router.patch("/{donor_id}", response_model=DonorResponse)
async def update_donor(
    donor_id: UUID,
    donor_data: DonorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a donor."""
    donor_service = DonorService(db)
    donor = await donor_service.get_by_id(donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    if donor_data.donor_code and donor_data.donor_code != donor.donor_code:
        existing = await donor_service.get_by_code(donor_data.donor_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Donor code already exists",
            )

    if donor_data.email and donor_data.email != donor.email:
        existing = await donor_service.get_by_email(donor_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    return await donor_service.update(donor, donor_data, updated_by=current_user.username)


@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donor(
    donor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a donor."""
    donor_service = DonorService(db)
    donor = await donor_service.get_by_id(donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )
    await donor_service.delete(donor)

