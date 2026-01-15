import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.donor import Donor
from app.schemas.donor import DonorCreate, DonorUpdate

logger = logging.getLogger(__name__)


class DonorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, donor_id: UUID) -> Donor | None:
        result = await self.db.execute(select(Donor).where(Donor.id == donor_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, donor_code: str) -> Donor | None:
        result = await self.db.execute(
            select(Donor).where(Donor.donor_code == donor_code)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Donor | None:
        result = await self.db.execute(select(Donor).where(Donor.email == email))
        return result.scalar_one_or_none()

    async def list_donors(
        self,
        page: int = 1,
        size: int = 10,
        donor_type: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Donor], int]:
        logger.info(f"Listing donors: page={page}, size={size}, donor_type={donor_type}")
        query = select(Donor)
        count_query = select(func.count(Donor.id))

        if donor_type:
            query = query.where(Donor.donor_type == donor_type)
            count_query = count_query.where(Donor.donor_type == donor_type)

        if is_active is not None:
            query = query.where(Donor.is_active == is_active)
            count_query = count_query.where(Donor.is_active == is_active)

        if search:
            search_filter = Donor.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Donor.name)
        result = await self.db.execute(query)
        donors = list(result.scalars().all())

        return donors, total

    async def create(self, data: DonorCreate, created_by: str) -> Donor:
        logger.info(f"Creating donor: {data.name}")
        donor = Donor(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(donor)
        await self.db.commit()
        await self.db.refresh(donor)
        logger.info(f"Created donor with ID: {donor.id}")
        return donor

    async def update(self, donor: Donor, data: DonorUpdate, updated_by: str) -> Donor:
        logger.info(f"Updating donor: {donor.id}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(donor, field, value)
        donor.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(donor)
        return donor

    async def delete(self, donor: Donor) -> None:
        logger.info(f"Deleting donor: {donor.id}")
        await self.db.delete(donor)
        await self.db.commit()

