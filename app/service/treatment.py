import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.model.treatment import Treatment
from app.model.patient import Patient
from app.model.partner import Partner
from app.schema.treatment import TreatmentCreate, TreatmentUpdate

logger = logging.getLogger("medbase.service.treatment")


class TreatmentService:
    """Service layer for treatment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, treatment_id: int) -> Optional[Treatment]:
        """Get treatment by ID."""
        result = await self.db.execute(
            select(Treatment).where(
                Treatment.id == treatment_id,
                Treatment.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_names(self, treatment_id: int) -> Optional[dict]:
        """Get treatment by ID with patient and partner names."""
        result = await self.db.execute(
            select(
                Treatment,
                func.concat(Patient.first_name, ' ', Patient.last_name).label("patient_name"),
                Partner.name.label("partner_name"),
            )
            .outerjoin(Patient, Treatment.patient_id == Patient.id)
            .outerjoin(Partner, Treatment.partner_id == Partner.id)
            .where(
                Treatment.id == treatment_id,
                Treatment.is_deleted == False,
            )
        )
        row = result.one_or_none()
        if not row:
            return None

        treatment = row[0]
        return {
            "id": treatment.id,
            "patient_id": treatment.patient_id,
            "appointment_id": treatment.appointment_id,
            "partner_id": treatment.partner_id,
            "treatment_type": treatment.treatment_type,
            "description": treatment.description,
            "treatment_date": treatment.treatment_date,
            "status": treatment.status,
            "cost": treatment.cost,
            "notes": treatment.notes,
            "is_deleted": treatment.is_deleted,
            "created_by": treatment.created_by,
            "created_at": treatment.created_at,
            "updated_by": treatment.updated_by,
            "updated_at": treatment.updated_at,
            "patient_name": row[1],
            "partner_name": row[2],
        }

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        patient_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        appointment_id: Optional[int] = None,
        status: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[dict], int]:
        """Get all treatments with pagination and filtering."""
        query = (
            select(
                Treatment,
                func.concat(Patient.first_name, ' ', Patient.last_name).label("patient_name"),
                Partner.name.label("partner_name"),
            )
            .outerjoin(Patient, Treatment.patient_id == Patient.id)
            .outerjoin(Partner, Treatment.partner_id == Partner.id)
            .where(Treatment.is_deleted == False)
        )

        count_subq = select(Treatment.id).where(Treatment.is_deleted == False)

        if patient_id is not None:
            query = query.where(Treatment.patient_id == patient_id)
            count_subq = count_subq.where(Treatment.patient_id == patient_id)
        if partner_id is not None:
            query = query.where(Treatment.partner_id == partner_id)
            count_subq = count_subq.where(Treatment.partner_id == partner_id)
        if appointment_id is not None:
            query = query.where(Treatment.appointment_id == appointment_id)
            count_subq = count_subq.where(Treatment.appointment_id == appointment_id)
        if status is not None:
            query = query.where(Treatment.status == status)
            count_subq = count_subq.where(Treatment.status == status)

        count_query = select(func.count()).select_from(count_subq.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(Treatment, sort, Treatment.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        treatments = []
        for row in rows:
            t = row[0]
            treatments.append({
                "id": t.id,
                "patient_id": t.patient_id,
                "appointment_id": t.appointment_id,
                "partner_id": t.partner_id,
                "treatment_type": t.treatment_type,
                "description": t.description,
                "treatment_date": t.treatment_date,
                "status": t.status,
                "cost": t.cost,
                "notes": t.notes,
                "is_deleted": t.is_deleted,
                "created_by": t.created_by,
                "created_at": t.created_at,
                "updated_by": t.updated_by,
                "updated_at": t.updated_at,
                "patient_name": row[1],
                "partner_name": row[2],
            })

        logger.debug("Queried treatments: total=%d returned=%d", total, len(treatments))
        return treatments, total

    async def create(self, data: TreatmentCreate, created_by: Optional[str] = None) -> Treatment:
        """Create a new treatment."""
        treatment = Treatment(
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            partner_id=data.partner_id,
            treatment_type=data.treatment_type,
            description=data.description,
            treatment_date=data.treatment_date,
            status=data.status,
            cost=data.cost,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(treatment)
        await self.db.flush()
        await self.db.refresh(treatment)

        logger.info("Created treatment id=%d patient_id=%d partner_id=%d", treatment.id, data.patient_id, data.partner_id)
        return treatment

    async def update(self, treatment_id: int, data: TreatmentUpdate, updated_by: Optional[str] = None) -> Optional[Treatment]:
        """Update a treatment."""
        treatment = await self.get_by_id(treatment_id)
        if not treatment:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(treatment, field, value)

        treatment.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(treatment)

        logger.info("Updated treatment id=%d fields=%s", treatment_id, list(update_data.keys()))
        return treatment

    async def update_status(self, treatment_id: int, status: str, updated_by: Optional[str] = None) -> Optional[Treatment]:
        """Update treatment status."""
        treatment = await self.get_by_id(treatment_id)
        if not treatment:
            return None

        treatment.status = status
        treatment.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(treatment)

        logger.info("Updated treatment id=%d status=%s", treatment_id, status)
        return treatment

    async def delete(self, treatment_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a treatment."""
        treatment = await self.get_by_id(treatment_id)
        if not treatment:
            return False
        treatment.is_deleted = True
        treatment.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted treatment id=%d", treatment_id)
        return True
