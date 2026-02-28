import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_user
from app.service.appointment import AppointmentService
from app.service.patient import PatientService
from app.service.doctor import DoctorService
from app.service.partner import PartnerService
from app.schema.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
    AppointmentResponse,
    AppointmentDetailResponse,
    AppointmentStatus,
    AppointmentType,
    AppointmentLocation,
)
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User

logger = logging.getLogger("medbase.router.appointment")

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=PaginatedResponse[AppointmentResponse])
async def get_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor"),
    partner_id: Optional[int] = Query(None, description="Filter by partner"),
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status", description="Filter by status"),
    type_filter: Optional[AppointmentType] = Query(None, alias="type", description="Filter by type"),
    location: Optional[AppointmentLocation] = Query(None, description="Filter by location"),
    appointment_date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search in patient/doctor/partner names"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all appointments with pagination, filtering, and sorting."""
    logger.info("Listing appointments page=%d size=%d by user_id=%d", page, size, current_user.id)

    service = AppointmentService(db)
    appointments, total = await service.get_all(
        page=page, size=size, patient_id=patient_id,
        doctor_id=doctor_id, partner_id=partner_id,
        status=status_filter, type=type_filter,
        location=location, appointment_date=appointment_date,
        search=search, sort=sort, order=order,
    )

    logger.info("Returning %d appointments (total=%d)", len(appointments), total)
    return PaginatedResponse(items=appointments, total=total, page=page, size=size)


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get appointment by ID (includes vitals, record)."""
    logger.info("Fetching appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    service = AppointmentService(db)
    result = await service.get_by_id_with_details(appointment_id)
    if not result:
        logger.warning("Appointment not found appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return result


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new appointment."""
    logger.info("Creating appointment patient_id=%d by user_id=%d", data.patient_id, current_user.id)

    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(data.patient_id)
    if not patient:
        logger.warning("Patient not found patient_id=%d", data.patient_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Validate doctor exists if provided
    if data.doctor_id:
        doctor_service = DoctorService(db)
        doctor = await doctor_service.get_by_id(data.doctor_id)
        if not doctor:
            logger.warning("Doctor not found doctor_id=%d", data.doctor_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")

    # Validate partner exists if provided
    if data.partner_id:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            logger.warning("Partner not found partner_id=%d", data.partner_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Partner not found")

    # External appointments should have a partner
    if data.location == AppointmentLocation.EXTERNAL and not data.partner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="External appointments require a partner_id",
        )

    service = AppointmentService(db)
    appointment = await service.create(data, created_by=current_user.username)
    logger.info("Appointment created appointment_id=%d", appointment.id)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an appointment."""
    logger.info("Updating appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found for update appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed appointment",
        )

    # Validate patient if being changed
    if data.patient_id:
        patient_service = PatientService(db)
        patient = await patient_service.get_by_id(data.patient_id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient not found")

    # Validate doctor if being changed
    if data.doctor_id:
        doctor_service = DoctorService(db)
        doctor = await doctor_service.get_by_id(data.doctor_id)
        if not doctor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor not found")

    # Validate partner if being changed
    if data.partner_id:
        partner_service = PartnerService(db)
        partner = await partner_service.get_by_id(data.partner_id)
        if not partner:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Partner not found")

    updated = await service.update(appointment_id, data, updated_by=current_user.username)
    logger.info("Appointment updated appointment_id=%d", appointment_id)
    return updated


@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update appointment status."""
    logger.info("Updating appointment status appointment_id=%d status=%s by user_id=%d",
                appointment_id, data.status, current_user.id)

    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found for status update appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    updated = await service.update_status(appointment_id, data.status, updated_by=current_user.username)
    logger.info("Appointment status updated appointment_id=%d status=%s", appointment_id, data.status)
    return updated


@router.delete("/{appointment_id}", response_model=MessageResponse)
async def delete_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an appointment (soft delete)."""
    logger.info("Deleting appointment_id=%d by user_id=%d", appointment_id, current_user.id)

    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        logger.warning("Appointment not found for deletion appointment_id=%d", appointment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    await service.delete(appointment_id, deleted_by=current_user.username)
    logger.info("Appointment deleted appointment_id=%d", appointment_id)
    return MessageResponse(message="Appointment deleted successfully")
