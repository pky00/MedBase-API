import logging
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SystemSettingCreate, SystemSettingUpdate

logger = logging.getLogger(__name__)


class SystemSettingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, setting_id: UUID) -> SystemSetting | None:
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.id == setting_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, setting_key: str) -> SystemSetting | None:
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.setting_key == setting_key)
        )
        return result.scalar_one_or_none()

    async def list_settings(
        self, category: str | None = None, is_public: bool | None = None
    ) -> tuple[list[SystemSetting], int]:
        logger.info("Listing system settings")
        query = select(SystemSetting)
        count_query = select(func.count(SystemSetting.id))

        if category:
            query = query.where(SystemSetting.category == category)
            count_query = count_query.where(SystemSetting.category == category)

        if is_public is not None:
            query = query.where(SystemSetting.is_public == is_public)
            count_query = count_query.where(SystemSetting.is_public == is_public)

        query = query.order_by(SystemSetting.category, SystemSetting.setting_key)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        result = await self.db.execute(query)
        settings = list(result.scalars().all())
        return settings, total

    async def create(self, data: SystemSettingCreate, created_by: str) -> SystemSetting:
        logger.info(f"Creating system setting: {data.setting_key}")
        setting = SystemSetting(
            **data.model_dump(),
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def update(
        self, setting: SystemSetting, data: SystemSettingUpdate, updated_by: str
    ) -> SystemSetting:
        logger.info(f"Updating system setting: {setting.setting_key}")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setting, field, value)
        setting.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete(self, setting: SystemSetting) -> None:
        logger.info(f"Deleting system setting: {setting.setting_key}")
        await self.db.delete(setting)
        await self.db.commit()

