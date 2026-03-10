import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.third_party import ThirdParty
from app.model.patient import Patient
from app.model.doctor import Doctor
from app.model.partner import Partner
from app.model.user import User

logger = logging.getLogger("medbase.service.third_party")


class ThirdPartyService:
    """Service layer for third party operations.

    Third party records are created automatically when creating users, doctors,
    patients, or partners. This service provides read-only access and the
    internal create method used by other services.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[ThirdParty]:
        """Get third party by name."""
        result = await self.db.execute(
            select(ThirdParty).where(
                ThirdParty.name == name,
                ThirdParty.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, third_party_id: int) -> Optional[ThirdParty]:
        """Get third party by ID."""
        result = await self.db.execute(
            select(ThirdParty).where(
                ThirdParty.id == third_party_id,
                ThirdParty.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
        exclude_patients: bool = False,
        exclude_doctors: bool = False,
        exclude_partners: bool = False,
        exclude_users: bool = False,
    ) -> Tuple[List[ThirdParty], int]:
        """Get all third parties with pagination and filtering."""
        query = select(ThirdParty).where(ThirdParty.is_deleted == False)

        if exclude_patients:
            patient_tp_ids = select(Patient.third_party_id).where(Patient.is_deleted == False)
            query = query.where(ThirdParty.id.not_in(patient_tp_ids))
        if exclude_doctors:
            doctor_tp_ids = select(Doctor.third_party_id).where(Doctor.is_deleted == False)
            query = query.where(ThirdParty.id.not_in(doctor_tp_ids))
        if exclude_partners:
            partner_tp_ids = select(Partner.third_party_id).where(Partner.is_deleted == False)
            query = query.where(ThirdParty.id.not_in(partner_tp_ids))
        if exclude_users:
            user_tp_ids = select(User.third_party_id).where(User.is_deleted == False)
            query = query.where(ThirdParty.id.not_in(user_tp_ids))

        if is_active is not None:
            query = query.where(ThirdParty.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    ThirdParty.code.ilike(search_term),
                    ThirdParty.name.ilike(search_term),
                    ThirdParty.email.ilike(search_term),
                    ThirdParty.phone.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(ThirdParty, sort, ThirdParty.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        records = result.scalars().all()

        logger.debug("Queried third parties: total=%d returned=%d", total, len(records))
        return list(records), total

    async def create(
        self,
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
        created_by: Optional[str] = None,
    ) -> ThirdParty:
        """Create a third party record. Used internally by other services."""
        tp = ThirdParty(
            name=name,
            phone=phone,
            email=email,
            is_active=is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(tp)
        await self.db.flush()
        await self.db.refresh(tp)
        logger.info("Created third party id=%d name='%s'", tp.id, name)
        return tp

    async def update(
        self,
        third_party_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[ThirdParty]:
        """Update a third party record. Used internally by other services."""
        tp = await self.get_by_id(third_party_id)
        if not tp:
            return None

        if name is not None:
            tp.name = name
        if phone is not None:
            tp.phone = phone
        if email is not None:
            tp.email = email
        if is_active is not None:
            tp.is_active = is_active
        tp.updated_by = updated_by

        await self.db.flush()
        await self.db.refresh(tp)
        logger.info("Updated third party id=%d", third_party_id)
        return tp
