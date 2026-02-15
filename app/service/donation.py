import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.donation import Donation, DonationItem
from app.model.partner import Partner
from app.model.medicine import Medicine
from app.model.equipment import Equipment
from app.model.medical_device import MedicalDevice
from app.schema.donation import (
    DonationCreate,
    DonationUpdate,
    DonationResponse,
    DonationDetailResponse,
    DonationItemCreate,
    DonationItemUpdate,
    DonationItemResponse,
)
from app.schema.inventory import ItemType
from app.schema.inventory_transaction import InventoryTransactionCreate, TransactionType
from app.service.inventory_transaction import InventoryTransactionService

logger = logging.getLogger("medbase.service.donation")


class DonationService:
    """Service layer for donation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, donation_id: int) -> Optional[Donation]:
        """Get donation by ID."""
        result = await self.db.execute(
            select(Donation).where(
                Donation.id == donation_id,
                Donation.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, donation_id: int) -> Optional[DonationDetailResponse]:
        """Get donation by ID with partner name and items."""
        result = await self.db.execute(
            select(
                Donation,
                Partner.name.label("partner_name"),
            )
            .outerjoin(
                Partner,
                (Partner.id == Donation.partner_id)
                & (Partner.is_deleted == False),
            )
            .where(
                Donation.id == donation_id,
                Donation.is_deleted == False,
            )
        )
        row = result.first()
        if not row:
            return None

        donation = row[0]
        partner_name = row[1]

        # Get donation items with item names
        items = await self._get_items_with_names(donation_id)

        return DonationDetailResponse(
            id=donation.id,
            partner_id=donation.partner_id,
            donation_date=donation.donation_date,
            notes=donation.notes,
            is_deleted=donation.is_deleted,
            created_by=donation.created_by,
            created_at=donation.created_at,
            updated_by=donation.updated_by,
            updated_at=donation.updated_at,
            partner_name=partner_name,
            items=items,
        )

    async def _get_items_with_names(self, donation_id: int) -> List[DonationItemResponse]:
        """Get donation items with resolved item names."""
        result = await self.db.execute(
            select(DonationItem).where(
                DonationItem.donation_id == donation_id,
                DonationItem.is_deleted == False,
            ).order_by(DonationItem.id.asc())
        )
        items = result.scalars().all()

        item_responses = []
        for item in items:
            item_name = await self._resolve_item_name(item.item_type, item.item_id)
            item_responses.append(
                DonationItemResponse(
                    id=item.id,
                    donation_id=item.donation_id,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    is_deleted=item.is_deleted,
                    created_by=item.created_by,
                    created_at=item.created_at,
                    updated_by=item.updated_by,
                    updated_at=item.updated_at,
                    item_name=item_name,
                )
            )

        return item_responses

    async def _resolve_item_name(self, item_type: str, item_id: int) -> Optional[str]:
        """Resolve the name of an inventory item."""
        if item_type == ItemType.MEDICINE:
            result = await self.db.execute(
                select(Medicine.name).where(Medicine.id == item_id)
            )
        elif item_type == ItemType.EQUIPMENT:
            result = await self.db.execute(
                select(Equipment.name).where(Equipment.id == item_id)
            )
        elif item_type == ItemType.MEDICAL_DEVICE:
            result = await self.db.execute(
                select(MedicalDevice.name).where(MedicalDevice.id == item_id)
            )
        else:
            return None
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        partner_id: Optional[int] = None,
        donation_date: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[DonationResponse], int]:
        """Get all donations with pagination, filtering, and sorting."""
        query = (
            select(
                Donation,
                Partner.name.label("partner_name"),
            )
            .outerjoin(
                Partner,
                (Partner.id == Donation.partner_id)
                & (Partner.is_deleted == False),
            )
            .where(Donation.is_deleted == False)
        )

        # Apply filters
        if partner_id is not None:
            query = query.where(Donation.partner_id == partner_id)
        if donation_date is not None:
            query = query.where(Donation.donation_date == donation_date)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Donation.notes.ilike(search_term),
                    Partner.name.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(Donation, sort, Donation.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        rows = result.all()

        donations = []
        for row in rows:
            donation = row[0]
            donations.append(
                DonationResponse(
                    id=donation.id,
                    partner_id=donation.partner_id,
                    donation_date=donation.donation_date,
                    notes=donation.notes,
                    is_deleted=donation.is_deleted,
                    created_by=donation.created_by,
                    created_at=donation.created_at,
                    updated_by=donation.updated_by,
                    updated_at=donation.updated_at,
                    partner_name=row[1],
                )
            )

        logger.debug("Queried donations: total=%d returned=%d", total, len(donations))

        return donations, total

    async def create(
        self,
        data: DonationCreate,
        created_by: Optional[int] = None,
    ) -> Donation:
        """Create a new donation with optional items."""
        donation = Donation(
            partner_id=data.partner_id,
            donation_date=data.donation_date,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(donation)
        await self.db.flush()
        await self.db.refresh(donation)

        # Create donation items if provided
        if data.items:
            for item_data in data.items:
                await self._create_donation_item(
                    donation_id=donation.id,
                    data=item_data,
                    created_by=created_by,
                )

        logger.info("Created donation id=%d partner_id=%d", donation.id, donation.partner_id)
        return donation

    async def update(
        self,
        donation_id: int,
        data: DonationUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[Donation]:
        """Update a donation."""
        donation = await self.get_by_id(donation_id)
        if not donation:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(donation, field, value)

        donation.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(donation)
        logger.info("Updated donation id=%d fields=%s", donation_id, list(update_data.keys()))
        return donation

    async def delete(self, donation_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a donation and its items, and reverse inventory via transactions."""
        donation = await self.get_by_id(donation_id)
        if not donation:
            return False

        tx_service = InventoryTransactionService(self.db)

        # Soft delete all donation items and reverse inventory via transactions
        result = await self.db.execute(
            select(DonationItem).where(
                DonationItem.donation_id == donation_id,
                DonationItem.is_deleted == False,
            )
        )
        items = result.scalars().all()
        for item in items:
            # Create a reversal transaction (destruction type reverses the donation increase)
            await tx_service.create(
                InventoryTransactionCreate(
                    transaction_type=TransactionType.DESTRUCTION,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    notes=f"Reversal: donation {donation_id} deleted",
                ),
                created_by=deleted_by,
            )
            item.is_deleted = True
            item.updated_by = deleted_by

        donation.is_deleted = True
        donation.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted donation id=%d", donation_id)
        return True

    # --- Donation Items ---

    async def get_item_by_id(self, item_id: int) -> Optional[DonationItem]:
        """Get a donation item by ID."""
        result = await self.db.execute(
            select(DonationItem).where(
                DonationItem.id == item_id,
                DonationItem.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_items_for_donation(self, donation_id: int) -> List[DonationItemResponse]:
        """Get all items for a donation."""
        return await self._get_items_with_names(donation_id)

    async def add_item_to_donation(
        self,
        donation_id: int,
        data: DonationItemCreate,
        created_by: Optional[int] = None,
    ) -> DonationItem:
        """Add an item to a donation and create inventory transaction."""
        item = await self._create_donation_item(
            donation_id=donation_id,
            data=data,
            created_by=created_by,
        )
        logger.info(
            "Added item to donation donation_id=%d item_type='%s' item_id=%d qty=%d",
            donation_id, data.item_type, data.item_id, data.quantity,
        )
        return item

    async def update_item(
        self,
        item_id: int,
        data: DonationItemUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[DonationItem]:
        """Update a donation item and adjust inventory via transactions."""
        item = await self.get_item_by_id(item_id)
        if not item:
            return None

        old_quantity = item.quantity
        old_item_type = item.item_type
        old_item_id = item.item_id

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        new_quantity = item.quantity
        new_item_type = item.item_type
        new_item_id = item.item_id

        tx_service = InventoryTransactionService(self.db)

        if old_item_type != new_item_type or old_item_id != new_item_id:
            # Item changed: reverse old donation, apply new donation
            await tx_service.create(
                InventoryTransactionCreate(
                    transaction_type=TransactionType.DESTRUCTION,
                    item_type=old_item_type,
                    item_id=old_item_id,
                    quantity=old_quantity,
                    notes=f"Reversal: donation item {item_id} changed",
                ),
                created_by=updated_by,
            )
            await tx_service.create(
                InventoryTransactionCreate(
                    transaction_type=TransactionType.DONATION,
                    item_type=new_item_type,
                    item_id=new_item_id,
                    quantity=new_quantity,
                    notes=f"Updated donation item {item_id}",
                ),
                created_by=updated_by,
            )
        elif old_quantity != new_quantity:
            # Only quantity changed
            diff = new_quantity - old_quantity
            if diff > 0:
                await tx_service.create(
                    InventoryTransactionCreate(
                        transaction_type=TransactionType.DONATION,
                        item_type=new_item_type,
                        item_id=new_item_id,
                        quantity=diff,
                        notes=f"Donation item {item_id} quantity increased",
                    ),
                    created_by=updated_by,
                )
            elif diff < 0:
                await tx_service.create(
                    InventoryTransactionCreate(
                        transaction_type=TransactionType.DESTRUCTION,
                        item_type=new_item_type,
                        item_id=new_item_id,
                        quantity=abs(diff),
                        notes=f"Donation item {item_id} quantity decreased",
                    ),
                    created_by=updated_by,
                )

        item.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(item)
        logger.info("Updated donation item id=%d fields=%s", item_id, list(update_data.keys()))
        return item

    async def delete_item(self, item_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a donation item and reverse inventory via transaction."""
        item = await self.get_item_by_id(item_id)
        if not item:
            return False

        # Create reversal transaction
        tx_service = InventoryTransactionService(self.db)
        await tx_service.create(
            InventoryTransactionCreate(
                transaction_type=TransactionType.DESTRUCTION,
                item_type=item.item_type,
                item_id=item.item_id,
                quantity=item.quantity,
                notes=f"Reversal: donation item {item_id} deleted",
            ),
            created_by=deleted_by,
        )

        item.is_deleted = True
        item.updated_by = deleted_by
        await self.db.flush()
        logger.info("Soft-deleted donation item id=%d", item_id)
        return True

    async def _create_donation_item(
        self,
        donation_id: int,
        data: DonationItemCreate,
        created_by: Optional[int] = None,
    ) -> DonationItem:
        """Create a donation item and create an inventory transaction."""
        item = DonationItem(
            donation_id=donation_id,
            item_type=data.item_type,
            item_id=data.item_id,
            quantity=data.quantity,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        # Create inventory transaction (donation type increases inventory)
        tx_service = InventoryTransactionService(self.db)
        await tx_service.create(
            InventoryTransactionCreate(
                transaction_type=TransactionType.DONATION,
                item_type=data.item_type,
                item_id=data.item_id,
                quantity=data.quantity,
                notes=f"Donation item for donation {donation_id}",
            ),
            created_by=created_by,
        )

        return item

    async def validate_item_exists(self, item_type: str, item_id: int) -> bool:
        """Validate that the referenced inventory item exists."""
        if item_type == ItemType.MEDICINE:
            result = await self.db.execute(
                select(Medicine.id).where(Medicine.id == item_id, Medicine.is_deleted == False)
            )
        elif item_type == ItemType.EQUIPMENT:
            result = await self.db.execute(
                select(Equipment.id).where(Equipment.id == item_id, Equipment.is_deleted == False)
            )
        elif item_type == ItemType.MEDICAL_DEVICE:
            result = await self.db.execute(
                select(MedicalDevice.id).where(MedicalDevice.id == item_id, MedicalDevice.is_deleted == False)
            )
        else:
            return False
        return result.scalar_one_or_none() is not None
