"""Patient allergy management endpoints."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.schemas.patient_allergy import (
    PatientAllergyCreate,
    PatientAllergyUpdate,
    PatientAllergyResponse,
    PatientAllergyListResponse,
)
from app.services.patient_service import PatientService
from app.services.patient_allergy_service import PatientAllergyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients/{patient_id}/allergies", tags=["patient allergies"])


async def get_patient_or_404(patient_id: UUID, db: AsyncSession):
    """Helper to get patient or raise 404."""
    patient_service = PatientService(db)
    patient = await patient_service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient


@router.post("/", response_model=PatientAllergyResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_allergy(
    patient_id: UUID,
    allergy_data: PatientAllergyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new allergy for a patient."""
    logger.info(f"Creating allergy for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    allergy_service = PatientAllergyService(db)
    allergy = await allergy_service.create(patient_id, allergy_data)
    return allergy


@router.get("/", response_model=PatientAllergyListResponse)
async def list_patient_allergies(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all allergies for a patient."""
    logger.info(f"Listing allergies for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    allergy_service = PatientAllergyService(db)
    allergies, total = await allergy_service.list_by_patient(patient_id)
    
    return PatientAllergyListResponse(data=allergies, total=total)


@router.get("/{allergy_id}", response_model=PatientAllergyResponse)
async def get_patient_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific allergy by ID."""
    logger.info(f"Getting allergy {allergy_id} for patient {patient_id}")
    
    await get_patient_or_404(patient_id, db)
    
    allergy_service = PatientAllergyService(db)
    allergy = await allergy_service.get_by_id(allergy_id)
    
    if not allergy or allergy.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy not found"
        )
    
    return allergy


@router.patch("/{allergy_id}", response_model=PatientAllergyResponse)
async def update_patient_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    allergy_data: PatientAllergyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an allergy."""
    logger.info(f"Updating allergy {allergy_id} for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    allergy_service = PatientAllergyService(db)
    allergy = await allergy_service.get_by_id(allergy_id)
    
    if not allergy or allergy.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy not found"
        )
    
    updated_allergy = await allergy_service.update(allergy, allergy_data)
    return updated_allergy


@router.delete("/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an allergy."""
    logger.info(f"Deleting allergy {allergy_id} for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    allergy_service = PatientAllergyService(db)
    allergy = await allergy_service.get_by_id(allergy_id)
    
    if not allergy or allergy.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy not found"
        )
    
    await allergy_service.delete(allergy)

