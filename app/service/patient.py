import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.patient import Patient
from app.model.patient_document import PatientDocument
from app.schema.patient import PatientCreate, PatientUpdate
from app.service.third_party import ThirdPartyService
from app.schema.third_party import ThirdPartyType
from app.utility import storage

logger = logging.getLogger("medbase.service.patient")


def _document_to_dict(doc: PatientDocument) -> dict:
    """Convert a PatientDocument to a dict with file_url from Lightsail bucket."""
    return {
        "id": doc.id,
        "patient_id": doc.patient_id,
        "document_name": doc.document_name,
        "document_type": doc.document_type,
        "file_path": doc.file_path,
        "file_url": storage.get_file_url(doc.file_path),
        "upload_date": doc.upload_date,
        "is_deleted": doc.is_deleted,
        "created_by": doc.created_by,
        "created_at": doc.created_at,
        "updated_by": doc.updated_by,
        "updated_at": doc.updated_at,
    }


class PatientService:
    """Service layer for patient operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, first_name: str, last_name: str) -> Optional[Patient]:
        """Get patient by first_name and last_name."""
        result = await self.db.execute(
            select(Patient).where(
                Patient.first_name == first_name,
                Patient.last_name == last_name,
                Patient.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_documents(self, patient_id: int) -> Optional[Tuple[Patient, List[dict]]]:
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

        documents = [_document_to_dict(doc) for doc in docs]
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
        query = select(Patient).where(Patient.is_deleted == False)

        if is_active is not None:
            query = query.where(Patient.is_active == is_active)
        if gender is not None:
            query = query.where(Patient.gender == gender)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.phone.ilike(search_term),
                    Patient.email.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(Patient, sort, Patient.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        patients = list(result.scalars().all())

        logger.debug("Queried patients: total=%d returned=%d", total, len(patients))
        return patients, total

    async def create(self, data: PatientCreate, created_by: Optional[str] = None) -> Patient:
        """Create a new patient. Auto-creates a third_party record if third_party_id not provided."""
        tp_service = ThirdPartyService(self.db)
        full_name = f"{data.first_name} {data.last_name}"

        if data.third_party_id:
            tp = await tp_service.get_by_id(data.third_party_id)
            if not tp:
                raise ValueError("Third party not found")
            third_party_id = data.third_party_id
        else:
            tp = await tp_service.create(
                name=full_name,
                type=ThirdPartyType.PATIENT,
                phone=data.phone,
                email=data.email,
                is_active=data.is_active,
                created_by=created_by,
            )
            third_party_id = tp.id

        patient = Patient(
            third_party_id=third_party_id,
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
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

        logger.info("Created patient id=%d name='%s' third_party_id=%d", patient.id, full_name, third_party_id)
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
        await self.db.refresh(patient)

        # Sync third_party record
        tp_service = ThirdPartyService(self.db)
        tp_name = None
        if "first_name" in update_data or "last_name" in update_data:
            tp_name = f"{patient.first_name} {patient.last_name}"

        await tp_service.update(
            patient.third_party_id,
            name=tp_name,
            phone=update_data.get("phone"),
            email=update_data.get("email"),
            is_active=update_data.get("is_active"),
            updated_by=updated_by,
        )

        logger.info("Updated patient id=%d fields=%s", patient_id, list(update_data.keys()))
        return patient

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
