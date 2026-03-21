import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.medical_record import MedicalRecordService
from app.service.appointment import AppointmentService
from app.schema.medical_record import (
    MedicalRecordCreate,
    MedicalRecordUpdate,
    MedicalRecordResponse,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.medical_record")

router = APIRouter(tags=["Medical Records"])


@router.get("/medical-records", response_model=PaginatedResponse[MedicalRecordResponse])
async def get_medical_records(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    appointment_id: Optional[int] = Query(None, description="Filter by appointment"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all medical records with pagination and filtering.

    **Filters:**
    - **patient_id**: Filter by patient
    - **appointment_id**: Filter by appointment

    **Sorting:** Default `id asc`. Sortable fields validated server-side.

    **Errors:**
    - `401`: Not authenticated
    """
    logger.info("Listing medical records page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = MedicalRecordService(db)
    records, total = await service.get_all(
        page=page, size=size, patient_id=patient_id,
        appointment_id=appointment_id, sort=sort, order=order,
    )

    logger.info("Returning %d medical records (total=%d)", len(records), total)
    return PaginatedResponse(items=records, total=total, page=page, size=size)


@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single medical record by ID.

    Returns the record with the associated patient name.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Medical record not found
    """
    logger.info("Fetching medical_record_id=%d by user_id=%d", record_id, current_user.id)

    service = MedicalRecordService(db)
    result = await service.get_by_id_with_patient(record_id)
    if not result:
        logger.warning("Medical record not found record_id=%d", record_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found")

    return result


@router.get("/appointments/{appointment_id}/medical-record", response_model=MedicalRecordResponse)
async def get_medical_record_for_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the medical record for a specific appointment.

    Each appointment can have at most one medical record.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Appointment not found, or no medical record for this appointment
    """
    logger.info("Fetching medical record for appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    # Validate appointment exists
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    service = MedicalRecordService(db)
    record = await service.get_by_appointment_id(appointment_id)
    if not record:
        logger.warning("Medical record not found for appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found for this appointment")

    return record


@router.post("/appointments/{appointment_id}/medical-record", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record_for_appointment(
    appointment_id: int,
    data: MedicalRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a medical record for an appointment.

    Only one medical record is allowed per appointment.

    **Business Rules:**
    - Appointment must exist
    - Cannot add a medical record to a completed appointment
    - Only one medical record per appointment

    **Errors:**
    - `400`: Appointment is completed, or record already exists for this appointment
    - `401`: Not authenticated
    - `404`: Appointment not found
    """
    logger.info("Creating medical record for appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    # Validate appointment exists
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Cannot add record if appointment is completed
    if appointment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add medical record to a completed appointment",
        )

    # Check if medical record already exists for this appointment (one per appointment)
    service = MedicalRecordService(db)
    existing = await service.get_by_appointment_id(appointment_id)
    if existing:
        logger.warning("Medical record already exists for appointment_id=%d", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medical record already exists for this appointment",
        )

    record = await service.create(appointment_id, data, created_by=current_user.username)
    logger.info("Medical record created id=%d for appointment_id=%d", record.id, appointment_id)
    return record


@router.put("/medical-records/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: int,
    data: MedicalRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a medical record.

    All fields are optional — only provided fields are updated.

    **Business Rules:**
    - Cannot edit a medical record if the appointment is completed

    **Errors:**
    - `400`: Cannot edit record of a completed appointment
    - `401`: Not authenticated
    - `404`: Medical record not found
    """
    logger.info("Updating medical_record_id=%d by user_id=%d", record_id, current_user.id)

    service = MedicalRecordService(db)
    record = await service.get_by_id(record_id)
    if not record:
        logger.warning("Medical record not found for update record_id=%d", record_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found")

    # Cannot edit if appointment is completed
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(record.appointment_id)
    if appointment and appointment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit medical record of a completed appointment",
        )

    updated = await service.update(record_id, data, updated_by=current_user.username)
    logger.info("Medical record updated record_id=%d", record_id)
    return updated


@router.delete("/medical-records/{record_id}", response_model=MessageResponse)
async def delete_medical_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-delete a medical record.

    The record is marked as deleted but remains in the database.

    **Errors:**
    - `401`: Not authenticated
    - `404`: Medical record not found
    """
    logger.info("Deleting medical_record_id=%d by user_id=%d", record_id, current_user.id)

    service = MedicalRecordService(db)
    record = await service.get_by_id(record_id)
    if not record:
        logger.warning("Medical record not found for deletion record_id=%d", record_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found")

    await service.delete(record_id, deleted_by=current_user.username)
    logger.info("Medical record deleted record_id=%d", record_id)
    return MessageResponse(message="Medical record deleted successfully")
