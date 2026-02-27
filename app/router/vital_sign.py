import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.vital_sign import VitalSignService
from app.service.appointment import AppointmentService
from app.schema.vital_sign import (
    VitalSignCreate,
    VitalSignUpdate,
    VitalSignResponse,
)
from app.schema.base import MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.vital_sign")

router = APIRouter(tags=["Vital Signs"])


@router.get("/appointments/{appointment_id}/vitals", response_model=VitalSignResponse)
async def get_vitals_for_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vital signs for an appointment."""
    logger.info("Fetching vitals for appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    # Validate appointment exists
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    service = VitalSignService(db)
    vital_signs = await service.get_by_appointment_id(appointment_id)
    if not vital_signs:
        logger.warning("Vital signs not found for appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital signs not found for this appointment")

    return vital_signs


@router.post("/appointments/{appointment_id}/vitals", response_model=VitalSignResponse, status_code=status.HTTP_201_CREATED)
async def create_vitals_for_appointment(
    appointment_id: int,
    data: VitalSignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add vital signs to an appointment. One vital signs record per appointment."""
    logger.info("Creating vitals for appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    # Validate appointment exists
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Cannot add vitals if appointment is completed
    if appointment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add vital signs to a completed appointment",
        )

    # Check if vital signs already exist for this appointment (one per appointment)
    service = VitalSignService(db)
    existing = await service.get_by_appointment_id(appointment_id)
    if existing:
        logger.warning("Vital signs already exist for appointment_id=%d", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vital signs already exist for this appointment",
        )

    vital_signs = await service.create(appointment_id, data, created_by=current_user.username)
    logger.info("Vital signs created id=%d for appointment_id=%d", vital_signs.id, appointment_id)
    return vital_signs


@router.put("/vital-signs/{vital_sign_id}", response_model=VitalSignResponse)
async def update_vital_signs(
    vital_sign_id: int,
    data: VitalSignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vital signs."""
    logger.info("Updating vital_sign_id=%d by user_id=%d", vital_sign_id, current_user.id)

    service = VitalSignService(db)
    vital_signs = await service.get_by_id(vital_sign_id)
    if not vital_signs:
        logger.warning("Vital signs not found vital_sign_id=%d", vital_sign_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital signs not found")

    # Cannot edit if appointment is completed
    appt_service = AppointmentService(db)
    appointment = await appt_service.get_by_id(vital_signs.appointment_id)
    if appointment and appointment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit vital signs of a completed appointment",
        )

    updated = await service.update(vital_sign_id, data, updated_by=current_user.username)
    logger.info("Vital signs updated vital_sign_id=%d", vital_sign_id)
    return updated


@router.delete("/vital-signs/{vital_sign_id}", response_model=MessageResponse)
async def delete_vital_signs(
    vital_sign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete vital signs (soft delete)."""
    logger.info("Deleting vital_sign_id=%d by user_id=%d", vital_sign_id, current_user.id)

    service = VitalSignService(db)
    vital_signs = await service.get_by_id(vital_sign_id)
    if not vital_signs:
        logger.warning("Vital signs not found for deletion vital_sign_id=%d", vital_sign_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vital signs not found")

    await service.delete(vital_sign_id, deleted_by=current_user.username)
    logger.info("Vital signs deleted vital_sign_id=%d", vital_sign_id)
    return MessageResponse(message="Vital signs deleted successfully")
