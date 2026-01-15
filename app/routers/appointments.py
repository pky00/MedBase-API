from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.enums import AppointmentStatus
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
)
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new appointment."""
    # Validate patient exists
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(appointment_data.patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient not found",
        )

    # Validate doctor exists
    doctor_service = DoctorService(db)
    doctor = await doctor_service.get_by_id(appointment_data.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor not found",
        )

    service = AppointmentService(db)
    return await service.create(appointment_data, created_by=current_user.username)


@router.get("/", response_model=AppointmentListResponse)
async def list_appointments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    patient_id: UUID | None = None,
    doctor_id: UUID | None = None,
    status: AppointmentStatus | None = None,
    appointment_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all appointments with pagination and filtering."""
    service = AppointmentService(db)
    appointments, total = await service.list_appointments(
        page=page,
        size=size,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=status,
        appointment_date=appointment_date,
        date_from=date_from,
        date_to=date_to,
    )
    return AppointmentListResponse(data=appointments, total=total, page=page, size=size)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific appointment by ID."""
    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an appointment."""
    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    if appointment_data.patient_id:
        patient_service = PatientService(db)
        patient = await patient_service.get_by_id(appointment_data.patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient not found",
            )

    if appointment_data.doctor_id:
        doctor_service = DoctorService(db)
        doctor = await doctor_service.get_by_id(appointment_data.doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor not found",
            )

    return await service.update(appointment, appointment_data, updated_by=current_user.username)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an appointment."""
    service = AppointmentService(db)
    appointment = await service.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    await service.delete(appointment)

