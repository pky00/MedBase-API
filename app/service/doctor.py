import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.doctor import Doctor
from app.model.partner import Partner
from app.schema.doctor import DoctorCreate, DoctorUpdate, DoctorDetailResponse

logger = logging.getLogger("medbase.service.doctor")


class DoctorService:
    """Service layer for doctor operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Doctor]:
        """Get doctor by name."""
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.name == name,
                Doctor.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID."""
        result = await self.db.execute(
            select(Doctor).where(
                Doctor.id == doctor_id,
                Doctor.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, doctor_id: int) -> Optional[DoctorDetailResponse]:
        """Get doctor by ID with partner name."""
        result = await self.db.execute(
            select(
                Doctor,
                Partner.name.label("partner_name"),
            )
            .outerjoin(
                Partner,
                (Partner.id == Doctor.partner_id)
                & (Partner.is_deleted == False),
            )
            .where(
                Doctor.id == doctor_id,
                Doctor.is_deleted == False,
            )
        )
        row = result.first()
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
        query = select(Doctor).where(Doctor.is_deleted == False)

        # Apply filters
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
                    Doctor.name.ilike(search_term),
                    Doctor.specialization.ilike(search_term),
                    Doctor.email.ilike(search_term),
                    Doctor.phone.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Doctor, sort, Doctor.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        doctors = result.scalars().all()

        logger.debug("Queried doctors: total=%d returned=%d", total, len(doctors))

        return list(doctors), total

    async def create(
        self, data: DoctorCreate, created_by: Optional[int] = None
    ) -> Doctor:
        """Create a new doctor."""
        doctor = Doctor(
            name=data.name,
            specialization=data.specialization,
            phone=data.phone,
            email=data.email,
            type=data.type,
            partner_id=data.partner_id,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(doctor)
        await self.db.flush()
        await self.db.refresh(doctor)

        logger.info("Created doctor id=%d name='%s'", doctor.id, doctor.name)
        return doctor

    async def update(
        self,
        doctor_id: int,
        data: DoctorUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[Doctor]:
        """Update a doctor."""
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doctor, field, value)

        doctor.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(doctor)
        logger.info("Updated doctor id=%d fields=%s", doctor_id, list(update_data.keys()))
        return doctor

    async def delete(self, doctor_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a doctor."""
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return False

        doctor.is_deleted = True
        doctor.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted doctor id=%d", doctor_id)
        return True
