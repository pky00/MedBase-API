import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.doctor import DoctorService
from app.service.partner import PartnerService
from app.service.third_party import ThirdPartyService
from app.schema.doctor import (
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    DoctorDetailResponse,
    DoctorType,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.doctor")

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=PaginatedResponse[DoctorResponse])
async def get_doctors(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    type: Optional[DoctorType] = Query(None, description="Filter by doctor type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    partner_id: Optional[int] = Query(None, description="Filter by partner ID"),
    search: Optional[str] = Query(None, description="Search in name, specialization, email, phone"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all doctors with pagination, filtering, and sorting.

    Returns a paginated list of doctors with their third party details (name, phone, email).

    **Filters:**
    - **type**: `internal`, `external`, `partner_provided`
    - **is_active**: `true` / `false`
    - **partner_id**: Filter by associated partner

    **Search:** Searches in name, specialization, email, and phone.

    **Sorting:** Default `id asc`. Sortable fields validated server-side.

    **Errors:**
    - `401`: Not authenticated
    """
    logger.info("Listing doctors page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = DoctorService(db)
    doctors, total = await service.get_all(
        page=page,
        size=size,
        type=type,
        is_active=is_active,
        partner_id=partner_id,
        search=search,
        sort=sort,
        order=order,
    )

    logger.info("Returning %d doctors (total=%d)", len(doctors), total)

    return PaginatedResponse(
        items=doctors, total=total, page=page, size=size,
    )


@router.get("/{doctor_id}", response_model=DoctorDetailResponse)
async def get_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single doctor by ID with details.

    Returns doctor info including third party details (name, phone, email) and
    the associated partner name if the doctor is partner-provided.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Doctor not found
    """
    logger.info("Fetching doctor_id=%d by user_id=%d", doctor_id, current_user.id)

    service = DoctorService(db)
    detail = await service.get_by_id_with_details(doctor_id)

    if not detail:
        logger.warning("Doctor not found doctor_id=%d", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    return detail


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    data: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new doctor.

    If `third_party_id` is provided, links to an existing third party record.
    Otherwise, a new third party is auto-created using the provided `name`, `phone`, and `email`.

    **Business Rules:**
    - Name must be unique across all third parties (when creating new)
    - If `type` is `partner_provided`, `partner_id` is required
    - Partner must exist if `partner_id` is provided

    **Errors:**
    - `400`: Name already exists, third party not found, or partner_provided missing partner_id
    - `401`: Not authenticated
    """
    logger.info(
        "Creating doctor name='%s' type='%s' by user_id=%d",
        data.name, data.type, current_user.id,
    )

    service = DoctorService(db)

    # Validate third_party_id if provided, otherwise check name uniqueness
    if data.third_party_id:
        tp_service = ThirdPartyService(db)
        tp = await tp_service.get_by_id(data.third_party_id)
        if not tp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Third party not found",
            )
    else:
        if not data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name is required when not providing a third_party_id",
            )
        existing = await service.get_by_name(data.name)
        if existing:
            logger.warning("Third party name already exists name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Third party name already exists",
            )
        tp_service = ThirdPartyService(db)
        existing_tp = await tp_service.get_by_name(data.name)
        if existing_tp:
            logger.warning("Name already exists in third parties name='%s'", data.name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name already exists in third parties",
            )

    # If partner_provided, partner_id is required
    if data.type == DoctorType.PARTNER_PROVIDED and not data.partner_id:
        logger.warning("Partner ID required for partner_provided doctor")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner ID is required for partner_provided doctors",
        )

    # Validate partner if provided
    if data.partner_id is not None:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            logger.warning("Partner not found partner_id=%d", data.partner_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner not found",
            )

    doctor = await service.create(data, created_by=current_user.username)

    logger.info("Doctor created doctor_id=%d", doctor.id)
    return doctor


@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing doctor.

    All fields are optional — only provided fields are updated.

    **Business Rules:**
    - If type becomes `partner_provided`, `partner_id` must be set
    - Partner must exist if `partner_id` is provided

    **Errors:**
    - `400`: partner_provided type without partner_id, or partner not found
    - `401`: Not authenticated
    - `404`: Doctor not found
    """
    logger.info("Updating doctor_id=%d by user_id=%d", doctor_id, current_user.id)

    service = DoctorService(db)

    doctor = await service.get_by_id(doctor_id)
    if not doctor:
        logger.warning("Doctor not found for update doctor_id=%d", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    # Determine effective type after update
    effective_type = data.type if data.type is not None else doctor.type
    effective_partner_id = data.partner_id if data.partner_id is not None else doctor.partner_id

    # If partner_provided, partner_id is required
    if effective_type == DoctorType.PARTNER_PROVIDED and not effective_partner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner ID is required for partner_provided doctors",
        )

    # Validate partner if provided
    if data.partner_id is not None:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            logger.warning("Partner not found partner_id=%d", data.partner_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner not found",
            )

    updated = await service.update(doctor_id, data, updated_by=current_user.username)
    logger.info("Doctor updated doctor_id=%d", doctor_id)
    return updated


@router.delete("/{doctor_id}", response_model=MessageResponse)
async def delete_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a doctor.

    The doctor record is marked as deleted but remains in the database.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Doctor not found
    """
    logger.info("Deleting doctor_id=%d by user_id=%d", doctor_id, current_user.id)

    service = DoctorService(db)

    doctor = await service.get_by_id(doctor_id)
    if not doctor:
        logger.warning("Doctor not found for deletion doctor_id=%d", doctor_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    await service.delete(doctor_id, deleted_by=current_user.username)
    logger.info("Doctor deleted doctor_id=%d", doctor_id)
    return MessageResponse(message="Doctor deleted successfully")
