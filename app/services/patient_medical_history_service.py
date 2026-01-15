import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.patient_medical_history import PatientMedicalHistory
from app.schemas.patient_medical_history import PatientMedicalHistoryCreate, PatientMedicalHistoryUpdate
from app.utils.context import get_audit_user

logger = logging.getLogger(__name__)


class PatientMedicalHistoryService:
    """Service for patient medical history CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, history_id: UUID) -> PatientMedicalHistory | None:
        """Get medical history entry by ID."""
        result = await self.db.execute(
            select(PatientMedicalHistory).where(PatientMedicalHistory.id == history_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_patient(
        self, 
        patient_id: UUID,
        current_only: bool = False
    ) -> tuple[list[PatientMedicalHistory], int]:
        """Get all medical history for a patient."""
        logger.info(f"Listing medical history for patient: {patient_id}, current_only={current_only}")
        
        # Build query
        query = select(PatientMedicalHistory).where(PatientMedicalHistory.patient_id == patient_id)
        count_query = select(func.count(PatientMedicalHistory.id)).where(
            PatientMedicalHistory.patient_id == patient_id
        )
        
        if current_only:
            query = query.where(PatientMedicalHistory.is_current == True)
            count_query = count_query.where(PatientMedicalHistory.is_current == True)
        
        # Count total
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get medical history
        result = await self.db.execute(
            query.order_by(PatientMedicalHistory.diagnosis_date.desc().nulls_last())
        )
        history = list(result.scalars().all())
        
        logger.info(f"Found {len(history)} medical history entries for patient: {patient_id}")
        return history, total
    
    async def create(self, patient_id: UUID, data: PatientMedicalHistoryCreate) -> PatientMedicalHistory:
        """Create a new medical history entry for a patient."""
        logger.info(f"Creating medical history for patient {patient_id}: {data.condition_name}")
        
        new_history = PatientMedicalHistory(
            patient_id=patient_id,
            **data.model_dump(),
            created_by=get_audit_user(),
        )
        
        self.db.add(new_history)
        await self.db.commit()
        await self.db.refresh(new_history)
        
        logger.info(f"Created medical history: {new_history.id}")
        return new_history
    
    async def update(
        self, 
        history: PatientMedicalHistory, 
        data: PatientMedicalHistoryUpdate
    ) -> PatientMedicalHistory:
        """Update a medical history entry."""
        logger.info(f"Updating medical history: {history.id}")
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(history, field, value)
        
        history.updated_by = get_audit_user()
        await self.db.commit()
        await self.db.refresh(history)
        
        logger.info(f"Updated medical history: {history.id}")
        return history
    
    async def delete(self, history: PatientMedicalHistory) -> None:
        """Delete a medical history entry."""
        logger.info(f"Deleting medical history: {history.id}")
        
        await self.db.delete(history)
        await self.db.commit()
        
        logger.info(f"Deleted medical history: {history.id}")

