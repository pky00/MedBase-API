import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.model.medical_device import MedicalDevice
from app.model.medical_device_category import MedicalDeviceCategory
from app.model.inventory import Inventory
from app.schema.medical_device import MedicalDeviceCreate, MedicalDeviceUpdate, MedicalDeviceDetailResponse
from app.schema.enums import ItemType
from app.service.inventory import InventoryService

logger = logging.getLogger("medbase.service.medical_device")


class MedicalDeviceService:
    """Service layer for medical device operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Optional[MedicalDevice]:
        """Get medical device by name."""
        result = await self.db.execute(
            select(MedicalDevice).where(
                MedicalDevice.name == name,
                MedicalDevice.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, device_id: int) -> Optional[MedicalDevice]:
        """Get medical device by ID."""
        result = await self.db.execute(
            select(MedicalDevice).where(
                MedicalDevice.id == device_id,
                MedicalDevice.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_details(self, device_id: int) -> Optional[MedicalDeviceDetailResponse]:
        """Get medical device by ID with inventory and category info."""
        result = await self.db.execute(
            select(
                MedicalDevice,
                Inventory.quantity,
                MedicalDeviceCategory.name.label("category_name"),
            )
            .outerjoin(
                Inventory,
                (Inventory.item_type == ItemType.MEDICAL_DEVICE)
                & (Inventory.item_id == MedicalDevice.id)
                & (Inventory.is_deleted == False),
            )
            .outerjoin(
                MedicalDeviceCategory,
                (MedicalDeviceCategory.id == MedicalDevice.category_id)
                & (MedicalDeviceCategory.is_deleted == False),
            )
            .where(
                MedicalDevice.id == device_id,
                MedicalDevice.is_deleted == False,
            )
        )
        row = result.first()
        if not row:
            return None

        return MedicalDeviceDetailResponse.from_row(row)

    async def get_all(
        self,
        page: int = 1,
        size: int = 10,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        sort: str = "id",
        order: str = "asc",
    ) -> Tuple[List[MedicalDevice], int]:
        """Get all medical devices with pagination, filtering, and sorting."""
        query = select(MedicalDevice).where(MedicalDevice.is_deleted == False)

        # Apply filters
        if category_id is not None:
            query = query.where(MedicalDevice.category_id == category_id)
        if is_active is not None:
            query = query.where(MedicalDevice.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    MedicalDevice.name.ilike(search_term),
                    MedicalDevice.description.ilike(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(MedicalDevice, sort, MedicalDevice.id)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        devices = result.scalars().all()

        logger.debug("Queried medical devices: total=%d returned=%d", total, len(devices))

        return list(devices), total

    async def create(
        self, data: MedicalDeviceCreate, created_by: Optional[int] = None
    ) -> MedicalDevice:
        """Create a new medical device and its inventory record."""
        device = MedicalDevice(
            name=data.name,
            category_id=data.category_id,
            description=data.description,
            serial_number=data.serial_number,
            is_active=data.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)

        # Auto-create inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.create(
            item_type=ItemType.MEDICAL_DEVICE,
            item_id=device.id,
            quantity=0,
            created_by=created_by,
        )

        logger.info("Created medical device id=%d name='%s'", device.id, device.name)
        return device

    async def update(
        self,
        device_id: int,
        data: MedicalDeviceUpdate,
        updated_by: Optional[int] = None,
    ) -> Optional[MedicalDevice]:
        """Update a medical device."""
        device = await self.get_by_id(device_id)
        if not device:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        device.updated_by = updated_by
        await self.db.flush()
        await self.db.refresh(device)
        logger.info("Updated medical device id=%d fields=%s", device_id, list(update_data.keys()))
        return device

    async def delete(self, device_id: int, deleted_by: Optional[int] = None) -> bool:
        """Soft delete a medical device and its inventory record."""
        device = await self.get_by_id(device_id)
        if not device:
            return False

        device.is_deleted = True
        device.updated_by = deleted_by

        # Also soft-delete the inventory record
        inventory_service = InventoryService(self.db)
        await inventory_service.delete(ItemType.MEDICAL_DEVICE, device_id, deleted_by=deleted_by)

        await self.db.flush()
        logger.info("Soft-deleted medical device id=%d", device_id)
        return True

    async def get_inventory_quantity(self, device_id: int) -> int:
        """Get inventory quantity for a medical device."""
        inventory_service = InventoryService(self.db)
        inventory = await inventory_service.get_by_item(ItemType.MEDICAL_DEVICE, device_id)
        if inventory:
            return inventory.quantity
        return 0
