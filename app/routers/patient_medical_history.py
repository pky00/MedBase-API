"""Patient medical history management endpoints."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.schemas.patient_medical_history import (
    PatientMedicalHistoryCreate,
    PatientMedicalHistoryUpdate,
    PatientMedicalHistoryResponse,
    PatientMedicalHistoryListResponse,
)
from app.services.patient_service import PatientService
from app.services.patient_medical_history_service import PatientMedicalHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients/{patient_id}/medical-history", tags=["patient medical history"])


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


@router.post("/", response_model=PatientMedicalHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_medical_history(
    patient_id: UUID,
    history_data: PatientMedicalHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new medical history entry for a patient."""
    logger.info(f"Creating medical history for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    history_service = PatientMedicalHistoryService(db)
    history = await history_service.create(patient_id, history_data)
    return history


@router.get("/", response_model=PatientMedicalHistoryListResponse)
async def list_patient_medical_history(
    patient_id: UUID,
    current_only: bool = Query(False, description="Show only current conditions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all medical history for a patient."""
    logger.info(f"Listing medical history for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    history_service = PatientMedicalHistoryService(db)
    history, total = await history_service.list_by_patient(patient_id, current_only=current_only)
    
    return PatientMedicalHistoryListResponse(data=history, total=total)


@router.get("/{history_id}", response_model=PatientMedicalHistoryResponse)
async def get_patient_medical_history(
    patient_id: UUID,
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific medical history entry by ID."""
    logger.info(f"Getting medical history {history_id} for patient {patient_id}")
    
    await get_patient_or_404(patient_id, db)
    
    history_service = PatientMedicalHistoryService(db)
    history = await history_service.get_by_id(history_id)
    
    if not history or history.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical history entry not found"
        )
    
    return history


@router.patch("/{history_id}", response_model=PatientMedicalHistoryResponse)
async def update_patient_medical_history(
    patient_id: UUID,
    history_id: UUID,
    history_data: PatientMedicalHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a medical history entry."""
    logger.info(f"Updating medical history {history_id} for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    history_service = PatientMedicalHistoryService(db)
    history = await history_service.get_by_id(history_id)
    
    if not history or history.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical history entry not found"
        )
    
    updated_history = await history_service.update(history, history_data)
    return updated_history


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_medical_history(
    patient_id: UUID,
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a medical history entry."""
    logger.info(f"Deleting medical history {history_id} for patient {patient_id} by user: {current_user.username}")
    
    await get_patient_or_404(patient_id, db)
    
    history_service = PatientMedicalHistoryService(db)
    history = await history_service.get_by_id(history_id)
    
    if not history or history.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical history entry not found"
        )
    
    await history_service.delete(history)

