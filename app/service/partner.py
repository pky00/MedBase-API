import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.partner import Partner
from app.model.donation import Donation, DonationItem
from app.schema.partner import PartnerCreate, PartnerUpdate, DonationSummary, PartnerDetailResponse

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

    async def get_by_id_with_details(self, partner_id: int) -> Optional[PartnerDetailResponse]:
        """Get partner by ID with donations summary."""
        partner = await self.get_by_id(partner_id)
        if not partner:
            return None

        # Get donations for this partner
        donations_list = []
        if partner.partner_type in ("donor", "both"):
            result = await self.db.execute(
                select(
                    Donation,
                    func.count(DonationItem.id).label("item_count"),
                )
                .outerjoin(
                    DonationItem,
                    (DonationItem.donation_id == Donation.id)
                    & (DonationItem.is_deleted == False),
                )
                .where(
                    Donation.partner_id == partner_id,
                    Donation.is_deleted == False,
                )
                .group_by(Donation.id)
                .order_by(Donation.donation_date.desc())
            )
            rows = result.all()
            for row in rows:
                donation = row[0]
                donations_list.append(
                    DonationSummary(
                        id=donation.id,
                        donation_date=str(donation.donation_date),
                        notes=donation.notes,
                        item_count=row[1] or 0,
                    )
                )

        return PartnerDetailResponse(
            id=partner.id,
            name=partner.name,
            partner_type=partner.partner_type,
            organization_type=partner.organization_type,
            contact_person=partner.contact_person,
            phone=partner.phone,
            email=partner.email,
            address=partner.address,
            is_active=partner.is_active,
            is_deleted=partner.is_deleted,
            created_by=partner.created_by,
            created_at=partner.created_at,
            updated_by=partner.updated_by,
            updated_at=partner.updated_at,
            donations=donations_list,
        )

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

        # Apply filters
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

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Partner, sort, Partner.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        partners = result.scalars().all()

        logger.debug("Queried partners: total=%d returned=%d", total, len(partners))

        return list(partners), total

    async def create(
        self, data: PartnerCreate, created_by: Optional[int] = None
    ) -> Partner:
        """Create a new partner."""
        partner = Partner(
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

        logger.info("Created partner id=%d name='%s'", partner.id, partner.name)
        return partner

    async def update(
        self,
        partner_id: int,
        data: PartnerUpdate,
        updated_by: Optional[int] = None,
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
        logger.info("Updated partner id=%d fields=%s", partner_id, list(update_data.keys()))
        return partner

    async def delete(self, partner_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a partner."""
        partner = await self.get_by_id(partner_id)
        if not partner:
            return False

        partner.is_deleted = True
        partner.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted partner id=%d", partner_id)
        return True

    async def has_donations(self, partner_id: int) -> bool:
        """Check if a partner has any donations."""
        result = await self.db.execute(
            select(func.count()).select_from(
                select(Donation).where(
                    Donation.partner_id == partner_id,
                    Donation.is_deleted == False,
                ).subquery()
            )
        )
        count = result.scalar()
        return count > 0
