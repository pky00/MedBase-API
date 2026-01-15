import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.patient_allergy import PatientAllergy
from app.schemas.patient_allergy import PatientAllergyCreate, PatientAllergyUpdate
from app.utils.context import get_audit_user

logger = logging.getLogger(__name__)


class PatientAllergyService:
    """Service for patient allergy CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, allergy_id: UUID) -> PatientAllergy | None:
        """Get allergy by ID."""
        result = await self.db.execute(
            select(PatientAllergy).where(PatientAllergy.id == allergy_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_patient(self, patient_id: UUID) -> tuple[list[PatientAllergy], int]:
        """Get all allergies for a patient."""
        logger.info(f"Listing allergies for patient: {patient_id}")
        
        # Count total
        count_result = await self.db.execute(
            select(func.count(PatientAllergy.id)).where(PatientAllergy.patient_id == patient_id)
        )
        total = count_result.scalar()
        
        # Get allergies
        result = await self.db.execute(
            select(PatientAllergy)
            .where(PatientAllergy.patient_id == patient_id)
            .order_by(PatientAllergy.allergen)
        )
        allergies = list(result.scalars().all())
        
        logger.info(f"Found {len(allergies)} allergies for patient: {patient_id}")
        return allergies, total
    
    async def create(self, patient_id: UUID, data: PatientAllergyCreate) -> PatientAllergy:
        """Create a new allergy for a patient."""
        logger.info(f"Creating allergy for patient {patient_id}: {data.allergen}")
        
        new_allergy = PatientAllergy(
            patient_id=patient_id,
            **data.model_dump(),
            created_by=get_audit_user(),
        )
        
        self.db.add(new_allergy)
        await self.db.commit()
        await self.db.refresh(new_allergy)
        
        logger.info(f"Created allergy: {new_allergy.id}")
        return new_allergy
    
    async def update(self, allergy: PatientAllergy, data: PatientAllergyUpdate) -> PatientAllergy:
        """Update an allergy."""
        logger.info(f"Updating allergy: {allergy.id}")
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(allergy, field, value)
        
        allergy.updated_by = get_audit_user()
        await self.db.commit()
        await self.db.refresh(allergy)
        
        logger.info(f"Updated allergy: {allergy.id}")
        return allergy
    
    async def delete(self, allergy: PatientAllergy) -> None:
        """Delete an allergy."""
        logger.info(f"Deleting allergy: {allergy.id}")
        
        await self.db.delete(allergy)
        await self.db.commit()
        
        logger.info(f"Deleted allergy: {allergy.id}")

