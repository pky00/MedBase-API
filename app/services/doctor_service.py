import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from app.utils.context import get_audit_user

logger = logging.getLogger(__name__)


class DoctorService:
    """Service for doctor CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, doctor_id: UUID) -> Doctor | None:
        """Get doctor by ID."""
        result = await self.db.execute(select(Doctor).where(Doctor.id == doctor_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Doctor | None:
        """Get doctor by email."""
        result = await self.db.execute(select(Doctor).where(Doctor.email == email))
        return result.scalar_one_or_none()
    
    async def list_doctors(
        self, 
        page: int = 1, 
        size: int = 20,
        specialization: str | None = None
    ) -> tuple[list[Doctor], int]:
        """
        Get paginated list of doctors.
        Returns tuple of (doctors, total_count).
        """
        logger.info(f"Listing doctors: page={page}, size={size}, specialization={specialization}")
        
        # Build query
        query = select(Doctor)
        count_query = select(func.count(Doctor.id))
        
        # Filter by specialization if provided
        if specialization:
            query = query.where(Doctor.specialization.ilike(f"%{specialization}%"))
            count_query = count_query.where(Doctor.specialization.ilike(f"%{specialization}%"))
        
        # Count total
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get paginated doctors
        offset = (page - 1) * size
        result = await self.db.execute(
            query
            .order_by(Doctor.last_name, Doctor.first_name)
            .offset(offset)
            .limit(size)
        )
        doctors = list(result.scalars().all())
        
        logger.info(f"Found {len(doctors)} doctors (total: {total})")
        return doctors, total
    
    async def create(self, doctor_data: DoctorCreate) -> Doctor:
        """Create a new doctor."""
        logger.info(f"Creating doctor: {doctor_data.first_name} {doctor_data.last_name}")
        
        new_doctor = Doctor(
            **doctor_data.model_dump(),
            created_by=get_audit_user(),
        )
        
        self.db.add(new_doctor)
        await self.db.commit()
        await self.db.refresh(new_doctor)
        
        logger.info(f"Created doctor: {new_doctor.id}")
        return new_doctor
    
    async def update(self, doctor: Doctor, doctor_data: DoctorUpdate) -> Doctor:
        """Update doctor with provided data."""
        logger.info(f"Updating doctor: {doctor.id}")
        
        update_data = doctor_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(doctor, field, value)
        
        doctor.updated_by = get_audit_user()
        await self.db.commit()
        await self.db.refresh(doctor)
        
        logger.info(f"Updated doctor: {doctor.id}")
        return doctor
    
    async def delete(self, doctor: Doctor) -> None:
        """Delete a doctor."""
        logger.info(f"Deleting doctor: {doctor.id} ({doctor.first_name} {doctor.last_name})")
        
        await self.db.delete(doctor)
        await self.db.commit()
        
        logger.info(f"Deleted doctor: {doctor.id}")
