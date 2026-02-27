import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.medical_record import MedicalRecord
from app.model.appointment import Appointment
from app.model.patient import Patient
from app.schema.medical_record import MedicalRecordCreate, MedicalRecordUpdate

logger = logging.getLogger("medbase.service.medical_record")


class MedicalRecordService:
    """Service layer for medical record operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, record_id: int) -> Optional[MedicalRecord]:
        """Get medical record by ID."""
        result = await self.db.execute(
            select(MedicalRecord).where(
                MedicalRecord.id == record_id,
                MedicalRecord.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_patient(self, record_id: int) -> Optional[dict]:
        """Get medical record by ID with patient name."""
        result = await self.db.execute(
            select(
                MedicalRecord,
                func.concat(Patient.first_name, ' ', Patient.last_name).label("patient_name"),
            )
            .outerjoin(Appointment, MedicalRecord.appointment_id == Appointment.id)
            .outerjoin(Patient, Appointment.patient_id == Patient.id)
            .where(
                MedicalRecord.id == record_id,
                MedicalRecord.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None

        record = row[0]
        return {
            "id": record.id,
            "appointment_id": record.appointment_id,
            "chief_complaint": record.chief_complaint,
            "diagnosis": record.diagnosis,
            "treatment_notes": record.treatment_notes,
            "follow_up_date": record.follow_up_date,
            "is_deleted": record.is_deleted,
            "created_by": record.created_by,
            "created_at": record.created_at,
            "updated_by": record.updated_by,
            "updated_at": record.updated_at,
            "patient_name": row[1],
        }

    async def get_by_appointment_id(self, appointment_id: int) -> Optional[MedicalRecord]:
        """Get medical record for an appointment."""
        result = await self.db.execute(
            select(MedicalRecord).where(
                MedicalRecord.appointment_id == appointment_id,
                MedicalRecord.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get all medical records with pagination and filtering."""
        query = (
            select(
                MedicalRecord,
                func.concat(Patient.first_name, ' ', Patient.last_name).label("patient_name"),
            )
            .outerjoin(Appointment, MedicalRecord.appointment_id == Appointment.id)
            .outerjoin(Patient, Appointment.patient_id == Patient.id)
            .where(MedicalRecord.is_deleted == False)
        )

        count_subq = select(MedicalRecord.id).where(MedicalRecord.is_deleted == False)

        if patient_id is not None:
            query = query.where(Appointment.patient_id == patient_id)
            count_subq = count_subq.outerjoin(Appointment, MedicalRecord.appointment_id == Appointment.id).where(Appointment.patient_id == patient_id)
        if appointment_id is not None:
            query = query.where(MedicalRecord.appointment_id == appointment_id)
            count_subq = count_subq.where(MedicalRecord.appointment_id == appointment_id)

        count_query = select(func.count()).select_from(count_subq.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(MedicalRecord, sort, MedicalRecord.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        records = []
        for row in rows:
            rec = row[0]
            records.append({
                "id": rec.id,
                "appointment_id": rec.appointment_id,
                "chief_complaint": rec.chief_complaint,
                "diagnosis": rec.diagnosis,
                "treatment_notes": rec.treatment_notes,
                "follow_up_date": rec.follow_up_date,
                "is_deleted": rec.is_deleted,
                "created_by": rec.created_by,
                "created_at": rec.created_at,
                "updated_by": rec.updated_by,
                "updated_at": rec.updated_at,
                "patient_name": row[1],
            })

        logger.debug("Queried medical records: total=%d returned=%d", total, len(records))
        return records, total

    async def create(self, appointment_id: int, data: MedicalRecordCreate, created_by: Optional[str] = None) -> MedicalRecord:
        """Create a medical record for an appointment."""
        record = MedicalRecord(
            appointment_id=appointment_id,
            chief_complaint=data.chief_complaint,
            diagnosis=data.diagnosis,
            treatment_notes=data.treatment_notes,
            follow_up_date=data.follow_up_date,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)

        logger.info("Created medical record id=%d appointment_id=%d", record.id, appointment_id)
        return record

    async def update(self, record_id: int, data: MedicalRecordUpdate, updated_by: Optional[str] = None) -> Optional[MedicalRecord]:
        """Update a medical record."""
        record = await self.get_by_id(record_id)
        if not record:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)

        record.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(record)

        logger.info("Updated medical record id=%d fields=%s", record_id, list(update_data.keys()))
        return record

    async def delete(self, record_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a medical record."""
        record = await self.get_by_id(record_id)
        if not record:
            return False
        record.is_deleted = True
        record.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted medical record id=%d", record_id)
        return True
