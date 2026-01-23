import logging
from datetime import date, datetime
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.donation import Donation
from app.models.donation_medicine_item import DonationMedicineItem
from app.models.donation_equipment_item import DonationEquipmentItem
from app.models.donation_medical_device_item import DonationMedicalDeviceItem
from app.models.enums import DonationType
from app.schemas.donation import (
    DonationCreate,
    DonationUpdate,
    DonationMedicineItemCreate,
    DonationMedicineItemUpdate,
    DonationEquipmentItemCreate,
    DonationEquipmentItemUpdate,
    DonationMedicalDeviceItemCreate,
    DonationMedicalDeviceItemUpdate
)

logger = logging.getLogger(__name__)


class DonationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, donation_id: UUID) -> Donation | None:
        """Get donation by ID with items (filtering out deleted items)"""
        logger.info(f"Fetching donation with ID: {donation_id}")

        result = await self.db.execute(
            select(Donation)
            .options(
                selectinload(Donation.medicine_items).where(DonationMedicineItem.is_deleted == False),
                selectinload(Donation.equipment_items).where(DonationEquipmentItem.is_deleted == False),
                selectinload(Donation.medical_device_items).where(DonationMedicalDeviceItem.is_deleted == False)
            )
            .where(Donation.id == donation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, donation_number: str) -> Donation | None:
        result = await self.db.execute(
            select(Donation).where(Donation.donation_number == donation_number)
        )
        return result.scalar_one_or_none()

    async def _generate_donation_number(self) -> str:
        """Generate next donation number in format DON-YYYY-NNNNNN"""
        import datetime as dt
        year = dt.datetime.now().year
        prefix = f"DON-{year}-"
        
        result = await self.db.execute(
            select(func.count(Donation.id)).where(
                Donation.donation_number.like(f"{prefix}%")
            )
        )
        count = result.scalar() or 0
        return f"{prefix}{str(count + 1).zfill(6)}"

    async def list_donations(
        self,
        page: int = 1,
        size: int = 10,
        donor_id: UUID | None = None,
        donation_type: DonationType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Donation], int]:
        """List donations with items (filtering out deleted items)"""
        logger.info(f"Listing donations: page={page}, size={size}")

        query = select(Donation).options(
            selectinload(Donation.medicine_items).where(DonationMedicineItem.is_deleted == False),
            selectinload(Donation.equipment_items).where(DonationEquipmentItem.is_deleted == False),
            selectinload(Donation.medical_device_items).where(DonationMedicalDeviceItem.is_deleted == False)
        )
        count_query = select(func.count(Donation.id))

        if donor_id:
            query = query.where(Donation.donor_id == donor_id)
            count_query = count_query.where(Donation.donor_id == donor_id)

        if donation_type:
            query = query.where(Donation.donation_type == donation_type)
            count_query = count_query.where(Donation.donation_type == donation_type)

        if date_from:
            query = query.where(Donation.donation_date >= date_from)
            count_query = count_query.where(Donation.donation_date >= date_from)

        if date_to:
            query = query.where(Donation.donation_date <= date_to)
            count_query = count_query.where(Donation.donation_date <= date_to)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Donation.donation_date.desc())
        result = await self.db.execute(query)
        donations = list(result.scalars().all())

        return donations, total

    async def create(self, data: DonationCreate, created_by: str) -> Donation:
        logger.info(f"Creating donation from donor: {data.donor_id}")
        donation_number = await self._generate_donation_number()
        donation = Donation(
            **data.model_dump(),
            donation_number=donation_number,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(donation)
        await self.db.commit()
        await self.db.refresh(donation)
        logger.info(f"Created donation: {donation_number}")
        return donation

    async def update(
        self, donation: Donation, data: DonationUpdate, updated_by: str
    ) -> Donation:
        logger.info(f"Updating donation: {donation.donation_number}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(donation, field, value)
        donation.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(donation)
        return donation

    async def delete(self, donation: Donation) -> None:
        logger.info(f"Deleting donation: {donation.donation_number}")
        await self.db.delete(donation)
        await self.db.commit()

    # Medicine Item Management
    async def add_medicine_item(
        self,
        donation_id: UUID,
        item_data: DonationMedicineItemCreate,
        created_by: str
    ) -> DonationMedicineItem:
        """Add medicine item to donation"""
        logger.info(f"Adding medicine item to donation {donation_id}")

        item = DonationMedicineItem(
            **item_data.model_dump(),
            donation_id=donation_id,
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_medicine_item(
        self,
        item_id: UUID,
        item_data: DonationMedicineItemUpdate,
        updated_by: str
    ) -> DonationMedicineItem | None:
        """Update medicine item"""
        logger.info(f"Updating medicine item {item_id}")

        result = await self.db.execute(
            select(DonationMedicineItem).where(DonationMedicineItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        for key, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def soft_delete_medicine_item(
        self,
        item_id: UUID,
        updated_by: str
    ) -> bool:
        """Soft delete medicine item"""
        logger.info(f"Soft deleting medicine item {item_id}")

        result = await self.db.execute(
            select(DonationMedicineItem).where(DonationMedicineItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return False

        item.is_deleted = True
        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

    # Equipment Item Management
    async def add_equipment_item(
        self,
        donation_id: UUID,
        item_data: DonationEquipmentItemCreate,
        created_by: str
    ) -> DonationEquipmentItem:
        """Add equipment item to donation"""
        logger.info(f"Adding equipment item to donation {donation_id}")

        item = DonationEquipmentItem(
            **item_data.model_dump(),
            donation_id=donation_id,
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_equipment_item(
        self,
        item_id: UUID,
        item_data: DonationEquipmentItemUpdate,
        updated_by: str
    ) -> DonationEquipmentItem | None:
        """Update equipment item"""
        logger.info(f"Updating equipment item {item_id}")

        result = await self.db.execute(
            select(DonationEquipmentItem).where(DonationEquipmentItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        for key, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def soft_delete_equipment_item(
        self,
        item_id: UUID,
        updated_by: str
    ) -> bool:
        """Soft delete equipment item"""
        logger.info(f"Soft deleting equipment item {item_id}")

        result = await self.db.execute(
            select(DonationEquipmentItem).where(DonationEquipmentItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return False

        item.is_deleted = True
        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

    # Medical Device Item Management
    async def add_medical_device_item(
        self,
        donation_id: UUID,
        item_data: DonationMedicalDeviceItemCreate,
        created_by: str
    ) -> DonationMedicalDeviceItem:
        """Add medical device item to donation"""
        logger.info(f"Adding medical device item to donation {donation_id}")

        item = DonationMedicalDeviceItem(
            **item_data.model_dump(),
            donation_id=donation_id,
            created_by=created_by,
            updated_by=created_by
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_medical_device_item(
        self,
        item_id: UUID,
        item_data: DonationMedicalDeviceItemUpdate,
        updated_by: str
    ) -> DonationMedicalDeviceItem | None:
        """Update medical device item"""
        logger.info(f"Updating medical device item {item_id}")

        result = await self.db.execute(
            select(DonationMedicalDeviceItem).where(DonationMedicalDeviceItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return None

        for key, value in item_data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)

        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def soft_delete_medical_device_item(
        self,
        item_id: UUID,
        updated_by: str
    ) -> bool:
        """Soft delete medical device item"""
        logger.info(f"Soft deleting medical device item {item_id}")

        result = await self.db.execute(
            select(DonationMedicalDeviceItem).where(DonationMedicalDeviceItem.id == item_id)
        )
        item = result.scalar_one_or_none()

        if not item:
            return False

        item.is_deleted = True
        item.updated_by = updated_by
        item.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

