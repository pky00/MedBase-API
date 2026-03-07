import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.partner import Partner
from app.schema.partner import PartnerCreate, PartnerUpdate
from app.service.third_party import ThirdPartyService

logger = logging.getLogger("medbase.service.partner")


class PartnerService:
    """Service layer for partner operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[Partner]:
        """Get partner by name."""
        result = await self.db.execute(
            select(Partner).where(
                Partner.name == name,
                Partner.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get partner by ID."""
        result = await self.db.execute(
            select(Partner).where(
                Partner.id == partner_id,
                Partner.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        partner_type: Optional[str] = None,
        organization_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[Partner], int]:
        """Get all partners with pagination, filtering, and sorting."""
        query = select(Partner).where(Partner.is_deleted == False)

        if partner_type is not None:
            query = query.where(Partner.partner_type == partner_type)
        if organization_type is not None:
            query = query.where(Partner.organization_type == organization_type)
        if is_active is not None:
            query = query.where(Partner.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Partner.name.ilike(search_term),
                    Partner.contact_person.ilike(search_term),
                    Partner.email.ilike(search_term),
                    Partner.phone.ilike(search_term),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        sort_column = getattr(Partner, sort, Partner.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        partners = result.scalars().all()

        logger.debug("Queried partners: total=%d returned=%d", total, len(partners))
        return list(partners), total

    async def create(
        self, data: PartnerCreate, created_by: Optional[str] = None
    ) -> Partner:
        """Create a new partner. Auto-creates a third_party record if third_party_id not provided."""
        tp_service = ThirdPartyService(self.db)

        if data.third_party_id:
            # Link to existing third_party
            tp = await tp_service.get_by_id(data.third_party_id)
            if not tp:
                raise ValueError("Third party not found")
            third_party_id = data.third_party_id
        else:
            # Auto-create third_party
            tp = await tp_service.create(
                name=data.name,
                phone=data.phone,
                email=data.email,
                is_active=data.is_active,
                created_by=created_by,
            )
            third_party_id = tp.id

        partner = Partner(
            third_party_id=third_party_id,
            name=data.name,
            partner_type=data.partner_type,
            organization_type=data.organization_type,
            contact_person=data.contact_person,
            phone=data.phone,
            email=data.email,
            address=data.address,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(partner)
        await self.db.flush()
        await self.db.refresh(partner)

        logger.info("Created partner id=%d name='%s' third_party_id=%d", partner.id, partner.name, third_party_id)
        return partner

    async def update(
        self,
        partner_id: int,
        data: PartnerUpdate,
        updated_by: Optional[str] = None,
    ) -> Optional[Partner]:
        """Update a partner."""
        partner = await self.get_by_id(partner_id)
        if not partner:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(partner, field, value)

        partner.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(partner)

        # Sync third_party record
        tp_service = ThirdPartyService(self.db)
        await tp_service.update(
            partner.third_party_id,
            name=update_data.get("name"),
            phone=update_data.get("phone"),
            email=update_data.get("email"),
            is_active=update_data.get("is_active"),
            updated_by=updated_by,
        )

        logger.info("Updated partner id=%d fields=%s", partner_id, list(update_data.keys()))
        return partner

    async def delete(self, partner_id: int, deleted_by: Optional[str] = None) -> bool:
        """Soft delete a partner."""
        partner = await self.get_by_id(partner_id)
        if not partner:
            return False

        partner.is_deleted = True
        partner.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted partner id=%d", partner_id)
        return True
