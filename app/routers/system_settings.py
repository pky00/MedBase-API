from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.system_setting import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
    SystemSettingListResponse,
)
from app.services.system_setting_service import SystemSettingService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.post("/", response_model=SystemSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(
    setting_data: SystemSettingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new system setting."""
    service = SystemSettingService(db)

    existing = await service.get_by_key(setting_data.setting_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setting key already exists",
        )

    return await service.create(setting_data, created_by=current_user.username)


@router.get("/", response_model=SystemSettingListResponse)
async def list_settings(
    category: str | None = None,
    is_public: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all system settings."""
    service = SystemSettingService(db)
    settings, total = await service.list_settings(category=category, is_public=is_public)
    return SystemSettingListResponse(data=settings, total=total)


@router.get("/{setting_id}", response_model=SystemSettingResponse)
async def get_setting(
    setting_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific system setting by ID."""
    service = SystemSettingService(db)
    setting = await service.get_by_id(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    return setting


@router.get("/key/{setting_key}", response_model=SystemSettingResponse)
async def get_setting_by_key(
    setting_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific system setting by key."""
    service = SystemSettingService(db)
    setting = await service.get_by_key(setting_key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    return setting


@router.patch("/{setting_id}", response_model=SystemSettingResponse)
async def update_setting(
    setting_id: UUID,
    setting_data: SystemSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a system setting."""
    service = SystemSettingService(db)
    setting = await service.get_by_id(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )

    if not setting.is_editable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This setting is not editable",
        )

    return await service.update(setting, setting_data, updated_by=current_user.username)


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    setting_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a system setting."""
    service = SystemSettingService(db)
    setting = await service.get_by_id(setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    await service.delete(setting)

