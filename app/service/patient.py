import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import contains_eager

from app.model.patient import Patient
from app.model.patient_document import PatientDocument
from app.model.third_party import ThirdParty
from app.schema.patient import PatientCreate, PatientUpdate
from app.schema.patient_document import PatientDocumentResponse
from app.service.third_party import ThirdPartyService
from app.utility import storage

logger = logging.getLogger("medbase.service.patient")

class PatientService:
    """Service layer for patient operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Patient]:
        """Get patient by name (via third_party)."""
        result = await self.db.execute(
            select(Patient)
            .outerjoin(ThirdParty, Patient.third_party_id == ThirdParty.id)
            .options(contains_eager(Patient.third_party))
            .where(
                ThirdParty.name == name,
                Patient.is_deleted == False,
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_by_id(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        result = await self.db.execute(
            select(Patient)
            .outerjoin(ThirdParty, Patient.third_party_id == ThirdParty.id)
            .options(contains_eager(Patient.third_party))
            .where(
                Patient.id == patient_id,
                Patient.is_deleted == False,
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_by_id_with_documents(self, patient_id: int) -> Optional[Tuple[Patient, List[PatientDocumentResponse]]]:
        """Get patient by ID with documents.

        Returns (patient, documents_list) or None if not found.
        Each document dict includes file_url resolved from the Lightsail bucket.
        """
        patient = await self.get_by_id(patient_id)
        if not patient:
            return None

        result = await self.db.execute(
            select(PatientDocument).where(
                PatientDocument.patient_id == patient_id,
                PatientDocument.is_deleted == False,
            ).order_by(PatientDocument.id.asc())
        )
        docs = result.scalars().all()

        documents = [PatientDocumentResponse.from_model(doc, await storage.generate_presigned_url(doc.file_path, download_filename=doc.document_name)) for doc in docs]
        return patient, documents

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        is_active: Optional[bool] = None,
        gender: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Patient], int]:
        """Get all patients with pagination, filtering, and sorting."""
        query = (
            select(Patient)
            .outerjoin(ThirdParty, Patient.third_party_id == ThirdParty.id)
            .options(contains_eager(Patient.third_party))
            .where(Patient.is_deleted == False)
        )

        if is_active is not None:
            query = query.where(Patient.is_active == is_active)
        if gender is not None:
            query = query.where(Patient.gender == gender)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    ThirdParty.name.ilike(search_term),
                    ThirdParty.phone.ilike(search_term),
                    ThirdParty.email.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        tp_sort_map = {"name": ThirdParty.name, "phone": ThirdParty.phone, "email": ThirdParty.email}
        ALLOWED_SORT = {"id", "name", "phone", "email", "date_of_birth", "gender", "is_active", "created_at"}
        if sort not in ALLOWED_SORT:
            sort = "id"
        sort_column = tp_sort_map.get(sort, getattr(Patient, sort, Patient.id))
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        patients = list(result.unique().scalars().all())

        logger.debug("Queried patients: total=%d returned=%d", total, len(patients))
        return patients, total

    async def create(self, data: PatientCreate, created_by: Optional[str] = None) -> Patient:
        """Create a new patient. Auto-creates a third_party record if third_party_id not provided."""
        tp_service = ThirdPartyService(self.db)

        if data.third_party_id:
            tp = await tp_service.get_by_id(data.third_party_id)
            if not tp:
                raise ValueError("Third party not found")
            third_party_id = data.third_party_id
        else:
            tp = await tp_service.create(
                name=data.name,
                phone=data.phone,
                email=data.email,
                is_active=data.is_active,
                created_by=created_by,
            )
            third_party_id = tp.id

        patient = Patient(
            third_party_id=third_party_id,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            address=data.address,
            emergency_contact=data.emergency_contact,
            emergency_phone=data.emergency_phone,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(patient)
        await self.db.flush()
        await self.db.refresh(patient)
        patient.third_party = tp

        logger.info("Created patient id=%d name='%s' third_party_id=%d", patient.id, tp.name, third_party_id)
        return patient

    async def update(self, patient_id: int, data: PatientUpdate, updated_by: Optional[str] = None) -> Optional[Patient]:
        """Update a patient."""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(patient, field, value)
        patient.updated_by = updated_by

        await self.db.flush()
        logger.info("Updated patient id=%d fields=%s", patient_id, list(update_data.keys()))
        return await self.get_by_id(patient_id)

    async def delete(self, patient_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a patient."""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return False
        patient.is_deleted = True
        patient.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted patient id=%d", patient_id)
        return True
