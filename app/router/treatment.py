import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.treatment import TreatmentService
from app.service.patient import PatientService
from app.service.partner import PartnerService
from app.service.appointment import AppointmentService
from app.schema.treatment import (
    TreatmentCreate,
    TreatmentUpdate,
    TreatmentStatusUpdate,
    TreatmentResponse,
    TreatmentStatus,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.treatment")

router = APIRouter(prefix="/treatments", tags=["Treatments"])


@router.get("", response_model=PaginatedResponse[TreatmentResponse])
async def get_treatments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    partner_id: Optional[int] = Query(None, description="Filter by partner"),
    appointment_id: Optional[int] = Query(None, description="Filter by appointment"),
    status_filter: Optional[TreatmentStatus] = Query(None, alias="status", description="Filter by status"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all treatments with pagination and filtering.

    **Filters:**
    - **patient_id**: Filter by patient
    - **partner_id**: Filter by partner (referral organization)
    - **appointment_id**: Filter by linked appointment
    - **status**: `pending`, `completed`

    **Sorting:** Default `id asc`. Sortable fields validated server-side.

    **Errors:**
    - `401`: Not authenticated
    """
    logger.info("Listing treatments page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = TreatmentService(db)
    treatments, total = await service.get_all(
        page=page, size=size, patient_id=patient_id,
        partner_id=partner_id, appointment_id=appointment_id,
        status=status_filter, sort=sort, order=order,
    )

    logger.info("Returning %d treatments (total=%d)", len(treatments), total)
    return PaginatedResponse(items=treatments, total=total, page=page, size=size)


@router.get("/{treatment_id}", response_model=TreatmentResponse)
async def get_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single treatment by ID.

    Returns the treatment with resolved patient and partner names.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Treatment not found
    """
    logger.info("Fetching treatment_id=%d by user_id=%d", treatment_id, current_user.id)

    service = TreatmentService(db)
    result = await service.get_by_id_with_names(treatment_id)
    if not result:
        logger.warning("Treatment not found treatment_id=%d", treatment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment not found")

    return result


@router.post("", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    data: TreatmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new treatment.

    Treatments represent medical procedures performed by referral partners.
    Can optionally be linked to an appointment.

    **Business Rules:**
    - Patient must exist
    - Partner must exist and have `partner_type` of `referral` or `both`
    - Appointment must exist if `appointment_id` is provided

    **Errors:**
    - `400`: Patient not found, partner not found, partner not referral type, or appointment not found
    - `401`: Not authenticated
    """
    logger.info("Creating treatment patient_id=%d partner_id=%d by user_id=%d",
                data.patient_id, data.partner_id, current_user.id)

    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(data.patient_id)
    if not patient:
        logger.warning("Patient not found patient_id=%d", data.patient_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Validate partner exists and is referral type
    partner_service = PartnerService(db)
    partner = await partner_service.get_by_id(data.partner_id)
    if not partner:
        logger.warning("Partner not found partner_id=%d", data.partner_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Partner not found")

    if partner.partner_type not in ("referral", "both"):
        logger.warning("Partner is not a referral partner partner_id=%d type=%s", data.partner_id, partner.partner_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner must have partner_type of 'referral' or 'both'",
        )

    # Validate appointment exists if provided
    if data.appointment_id:
        appt_service = AppointmentService(db)
        appointment = await appt_service.get_by_id(data.appointment_id)
        if not appointment:
            logger.warning("Appointment not found appointment_id=%d", data.appointment_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment not found")

    service = TreatmentService(db)
    treatment = await service.create(data, created_by=current_user.username)
    logger.info("Treatment created treatment_id=%d", treatment.id)
    return treatment


@router.put("/{treatment_id}", response_model=TreatmentResponse)
async def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing treatment.

    All fields are optional — only provided fields are updated.

    **Business Rules:**
    - Patient must exist if changed
    - Partner must exist and be referral type if changed
    - Appointment must exist if changed

    **Errors:**
    - `400`: Referenced entity not found, or partner not referral type
    - `401`: Not authenticated
    - `404`: Treatment not found
    """
    logger.info("Updating treatment_id=%d by user_id=%d", treatment_id, current_user.id)

    service = TreatmentService(db)
    treatment = await service.get_by_id(treatment_id)
    if not treatment:
        logger.warning("Treatment not found for update treatment_id=%d", treatment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment not found")

    # Validate patient if being changed
    if data.patient_id:
        patient_service = PatientService(db)
        patient = await patient_service.get_by_id(data.patient_id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Validate partner if being changed
    if data.partner_id:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Partner not found")
        if partner.partner_type not in ("referral", "both"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner must have partner_type of 'referral' or 'both'",
            )

    # Validate appointment if being changed
    if data.appointment_id:
        appt_service = AppointmentService(db)
        appointment = await appt_service.get_by_id(data.appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment not found")

    updated = await service.update(treatment_id, data, updated_by=current_user.username)
    logger.info("Treatment updated treatment_id=%d", treatment_id)
    return updated


@router.put("/{treatment_id}/status", response_model=TreatmentResponse)
async def update_treatment_status(
    treatment_id: int,
    data: TreatmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update only the status of a treatment.

    **Valid statuses:** `pending`, `completed`

    **Errors:**
    - `401`: Not authenticated
    - `404`: Treatment not found
    """
    logger.info("Updating treatment status treatment_id=%d status=%s by user_id=%d",
                treatment_id, data.status, current_user.id)

    service = TreatmentService(db)
    treatment = await service.get_by_id(treatment_id)
    if not treatment:
        logger.warning("Treatment not found for status update treatment_id=%d", treatment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment not found")

    updated = await service.update_status(treatment_id, data.status, updated_by=current_user.username)
    logger.info("Treatment status updated treatment_id=%d status=%s", treatment_id, data.status)
    return updated


@router.delete("/{treatment_id}", response_model=MessageResponse)
async def delete_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a treatment.

    The treatment record is marked as deleted but remains in the database.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Treatment not found
    """
    logger.info("Deleting treatment_id=%d by user_id=%d", treatment_id, current_user.id)

    service = TreatmentService(db)
    treatment = await service.get_by_id(treatment_id)
    if not treatment:
        logger.warning("Treatment not found for deletion treatment_id=%d", treatment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment not found")

    await service.delete(treatment_id, deleted_by=current_user.username)
    logger.info("Treatment deleted treatment_id=%d", treatment_id)
    return MessageResponse(message="Treatment deleted successfully")
