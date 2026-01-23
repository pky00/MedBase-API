import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.utils.context import get_audit_user

logger = logging.getLogger(__name__)


class PatientService:
    """Service for patient CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, patient_id: UUID) -> Patient | None:
        """Get patient by ID."""
        result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()
    
    async def get_by_patient_number(self, patient_number: str) -> Patient | None:
        """Get patient by patient number."""
        result = await self.db.execute(
            select(Patient).where(Patient.patient_number == patient_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Patient | None:
        """Get patient by email."""
        result = await self.db.execute(select(Patient).where(Patient.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_national_id(self, national_id: str) -> Patient | None:
        """Get patient by national ID."""
        result = await self.db.execute(
            select(Patient).where(Patient.national_id == national_id)
        )
        return result.scalar_one_or_none()
    
    async def list_patients(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc"
    ) -> tuple[list[Patient], int]:
        """
        Get paginated list of patients.
        Search can match patient_number, first_name, last_name, phone, or email.
        Supports sorting by any patient field.
        Returns tuple of (patients, total_count).
        """
        logger.info(f"Listing patients: page={page}, size={size}, search={search}, sort_by={sort_by}, sort_order={sort_order}")

        # Build query
        query = select(Patient)
        count_query = select(func.count(Patient.id))

        # Filter by search term if provided
        if search:
            search_filter = (
                Patient.patient_number.ilike(f"%{search}%") |
                Patient.first_name.ilike(f"%{search}%") |
                Patient.last_name.ilike(f"%{search}%") |
                Patient.phone.ilike(f"%{search}%") |
                Patient.email.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Count total
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply sorting
        if sort_by and hasattr(Patient, sort_by):
            column = getattr(Patient, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # Default sorting
            query = query.order_by(Patient.last_name, Patient.first_name)

        # Get paginated patients
        offset = (page - 1) * size
        result = await self.db.execute(
            query
            .offset(offset)
            .limit(size)
        )
        patients = list(result.scalars().all())

        logger.info(f"Found {len(patients)} patients (total: {total})")
        return patients, total
    
    async def generate_patient_number(self) -> str:
        """Generate a unique patient number."""
        # Get the highest patient number
        result = await self.db.execute(
            select(func.max(Patient.patient_number))
        )
        max_number = result.scalar()
        
        if max_number is None:
            return "P000001"
        
        # Extract the numeric part and increment
        try:
            numeric_part = int(max_number[1:])  # Remove 'P' prefix
            new_number = numeric_part + 1
        except (ValueError, IndexError):
            new_number = 1
        
        return f"P{new_number:06d}"
    
    async def create(self, patient_data: PatientCreate) -> Patient:
        """Create a new patient with auto-generated patient number."""
        logger.info(f"Creating patient: {patient_data.first_name} {patient_data.last_name}")
        
        patient_number = await self.generate_patient_number()
        
        new_patient = Patient(
            patient_number=patient_number,
            **patient_data.model_dump(),
            created_by=get_audit_user(),
        )
        
        self.db.add(new_patient)
        await self.db.commit()
        await self.db.refresh(new_patient)
        
        logger.info(f"Created patient: {new_patient.id} ({patient_number})")
        return new_patient
    
    async def update(self, patient: Patient, patient_data: PatientUpdate) -> Patient:
        """Update patient with provided data."""
        logger.info(f"Updating patient: {patient.id}")
        
        update_data = patient_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(patient, field, value)
        
        patient.updated_by = get_audit_user()
        await self.db.commit()
        await self.db.refresh(patient)
        
        logger.info(f"Updated patient: {patient.id}")
        return patient
    
    async def delete(self, patient: Patient) -> None:
        """Delete a patient."""
        logger.info(f"Deleting patient: {patient.id} ({patient.patient_number})")
        
        await self.db.delete(patient)
        await self.db.commit()
        
        logger.info(f"Deleted patient: {patient.id}")

