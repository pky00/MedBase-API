from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.models.user import User
from app.schemas.doctor import (
    DoctorCreate,
    DoctorResponse,
    DoctorUpdate,
    DoctorListResponse,
)
from app.utils.dependencies import get_current_user
from app.services.doctor_service import DoctorService
from app.services.user_service import UserService

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_data: DoctorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new doctor."""
    doctor_service = DoctorService(db)
    
    # Validate email uniqueness if provided
    if doctor_data.email:
        if await doctor_service.get_by_email(doctor_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Validate user_id exists if provided
    if doctor_data.user_id:
        user_service = UserService(db)
        if not await user_service.get_by_id(doctor_data.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
    
    new_doctor = await doctor_service.create(doctor_data)
    return new_doctor


@router.get("/", response_model=DoctorListResponse)
async def list_doctors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    specialization: str | None = Query(None, description="Filter by specialization"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all doctors with pagination and optional filtering."""
    doctor_service = DoctorService(db)
    
    doctors, total = await doctor_service.list_doctors(
        page=page, 
        size=size,
        specialization=specialization
    )
    
    return DoctorListResponse(
        data=doctors,
        total=total,
        page=page,
        size=size
    )


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific doctor by ID."""
    doctor_service = DoctorService(db)
    
    doctor = await doctor_service.get_by_id(doctor_id)
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: UUID,
    doctor_data: DoctorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a doctor by ID."""
    doctor_service = DoctorService(db)
    
    doctor = await doctor_service.get_by_id(doctor_id)
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Validate email uniqueness if being updated
    if doctor_data.email and doctor_data.email != doctor.email:
        if await doctor_service.get_by_email(doctor_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Validate user_id exists if being updated
    if doctor_data.user_id:
        user_service = UserService(db)
        if not await user_service.get_by_id(doctor_data.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
    
    updated_doctor = await doctor_service.update(doctor, doctor_data)
    return updated_doctor


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(
    doctor_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a doctor by ID."""
    doctor_service = DoctorService(db)
    
    doctor = await doctor_service.get_by_id(doctor_id)
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    await doctor_service.delete(doctor)

