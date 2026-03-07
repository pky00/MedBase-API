import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import contains_eager, aliased

from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.third_party import ThirdParty
from app.schema.doctor import DoctorCreate, DoctorUpdate, DoctorDetailResponse
from app.service.third_party import ThirdPartyService

logger = logging.getLogger("medbase.service.doctor")

TP_FIELDS = {"name", "phone", "email"}


class DoctorService:
    """Service layer for doctor operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Doctor]:
        """Get doctor by name (via third_party)."""
        result = await self.db.execute(
            select(Doctor)
            .outerjoin(ThirdParty, Doctor.third_party_id == ThirdParty.id)
            .options(contains_eager(Doctor.third_party))
            .where(ThirdParty.name == name, Doctor.is_deleted == False)
        )
        return result.unique().scalar_one_or_none()

    async def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID."""
        result = await self.db.execute(
            select(Doctor)
            .outerjoin(ThirdParty, Doctor.third_party_id == ThirdParty.id)
            .options(contains_eager(Doctor.third_party))
            .where(Doctor.id == doctor_id, Doctor.is_deleted == False)
        )
        return result.unique().scalar_one_or_none()

    async def get_by_id_with_details(self, doctor_id: int) -> Optional[DoctorDetailResponse]:
        """Get doctor by ID with partner name."""
        PartnerTP = aliased(ThirdParty)
        result = await self.db.execute(
            select(Doctor, PartnerTP.name.label("partner_name"))
            .outerjoin(ThirdParty, Doctor.third_party_id == ThirdParty.id)
            .options(contains_eager(Doctor.third_party))
            .outerjoin(Partner, (Partner.id == Doctor.partner_id) & (Partner.is_deleted == False))
            .outerjoin(PartnerTP, Partner.third_party_id == PartnerTP.id)
            .where(Doctor.id == doctor_id, Doctor.is_deleted == False)
        )
        row = result.unique().first()
        if not row:
            return None
        return DoctorDetailResponse.from_row(row)

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        type: Optional[str] = None,
        is_active: Optional[bool] = None,
        partner_id: Optional[int] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Doctor], int]:
        """Get all doctors with pagination, filtering, and sorting."""
        query = (
            select(Doctor)
            .outerjoin(ThirdParty, Doctor.third_party_id == ThirdParty.id)
            .options(contains_eager(Doctor.third_party))
            .where(Doctor.is_deleted == False)
        )

        if type is not None:
            query = query.where(Doctor.type == type)
        if is_active is not None:
            query = query.where(Doctor.is_active == is_active)
        if partner_id is not None:
            query = query.where(Doctor.partner_id == partner_id)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    ThirdParty.name.ilike(search_term),
                    Doctor.specialization.ilike(search_term),
                    ThirdParty.email.ilike(search_term),
                    ThirdParty.phone.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        tp_sort_map = {"name": ThirdParty.name, "phone": ThirdParty.phone, "email": ThirdParty.email}
        sort_column = tp_sort_map.get(sort, getattr(Doctor, sort, Doctor.id))
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        doctors = result.unique().scalars().all()

        logger.debug("Queried doctors: total=%d returned=%d", total, len(doctors))
        return list(doctors), total

    async def create(self, data: DoctorCreate, created_by: Optional[str] = None) -> Doctor:
        """Create a new doctor. Auto-creates a third_party record if third_party_id not provided."""
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

        doctor = Doctor(
            third_party_id=third_party_id,
            specialization=data.specialization,
            type=data.type,
            partner_id=data.partner_id,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(doctor)
        await self.db.flush()
        await self.db.refresh(doctor)
        doctor.third_party = tp

        logger.info("Created doctor id=%d name='%s' third_party_id=%d", doctor.id, tp.name, third_party_id)
        return doctor

    async def update(self, doctor_id: int, data: DoctorUpdate, updated_by: Optional[str] = None) -> Optional[Doctor]:
        """Update a doctor."""
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Separate third_party fields
        tp_fields = {k: update_data.pop(k) for k in list(update_data) if k in TP_FIELDS}

        # Update entity fields
        for field, value in update_data.items():
            setattr(doctor, field, value)
        doctor.updated_by = updated_by

        # Update third_party fields
        if tp_fields:
            tp_service = ThirdPartyService(self.db)
            await tp_service.update(doctor.third_party_id, **tp_fields, updated_by=updated_by)

        await self.db.flush()
        logger.info("Updated doctor id=%d fields=%s", doctor_id, list(data.model_dump(exclude_unset=True).keys()))
        return await self.get_by_id(doctor_id)

    async def delete(self, doctor_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a doctor."""
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return False
        doctor.is_deleted = True
        doctor.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted doctor id=%d", doctor_id)
        return True
