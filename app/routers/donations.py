from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.enums import DonationType
from app.schemas.donation import (
    DonationCreate,
    DonationUpdate,
    DonationResponse,
    DonationListResponse,
    DonationMedicineItemCreate,
    DonationMedicineItemUpdate,
    DonationMedicineItemResponse,
    DonationEquipmentItemCreate,
    DonationEquipmentItemUpdate,
    DonationEquipmentItemResponse,
    DonationMedicalDeviceItemCreate,
    DonationMedicalDeviceItemUpdate,
    DonationMedicalDeviceItemResponse,
)
from app.services.donation_service import DonationService
from app.services.donor_service import DonorService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/donations", tags=["donations"])


@router.post("/", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    donation_data: DonationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new donation record."""
    # Validate donor exists
    donor_service = DonorService(db)
    donor = await donor_service.get_by_id(donation_data.donor_id)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Donor not found",
        )

    service = DonationService(db)
    return await service.create(donation_data, created_by=current_user.username)


@router.get("/", response_model=DonationListResponse)
async def list_donations(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    donor_id: UUID | None = None,
    donation_type: DonationType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all donations with pagination and filtering."""
    service = DonationService(db)
    donations, total = await service.list_donations(
        page=page,
        size=size,
        donor_id=donor_id,
        donation_type=donation_type,
        date_from=date_from,
        date_to=date_to,
    )
    return DonationListResponse(data=donations, total=total, page=page, size=size)


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific donation by ID."""
    service = DonationService(db)
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )
    return donation


@router.patch("/{donation_id}", response_model=DonationResponse)
async def update_donation(
    donation_id: UUID,
    donation_data: DonationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a donation."""
    service = DonationService(db)
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    return await service.update(donation, donation_data, updated_by=current_user.username)


@router.delete("/{donation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donation(
    donation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a donation."""
    service = DonationService(db)
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )
    await service.delete(donation)


# Medicine Item Endpoints
@router.post("/{donation_id}/medicine-items", response_model=DonationMedicineItemResponse, status_code=status.HTTP_201_CREATED)
async def add_medicine_item(
    donation_id: UUID,
    item_data: DonationMedicineItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add medicine item to donation."""
    service = DonationService(db)

    # Verify donation exists
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    item = await service.add_medicine_item(
        donation_id,
        item_data,
        created_by=current_user.username
    )
    return item


@router.patch("/{donation_id}/medicine-items/{item_id}", response_model=DonationMedicineItemResponse)
async def update_medicine_item(
    donation_id: UUID,
    item_id: UUID,
    item_data: DonationMedicineItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update medicine item."""
    service = DonationService(db)

    item = await service.update_medicine_item(
        item_id,
        item_data,
        updated_by=current_user.username
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine item not found",
        )

    return item


@router.delete("/{donation_id}/medicine-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine_item(
    donation_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete medicine item."""
    service = DonationService(db)

    success = await service.soft_delete_medicine_item(
        item_id,
        updated_by=current_user.username
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine item not found",
        )


# Equipment Item Endpoints
@router.post("/{donation_id}/equipment-items", response_model=DonationEquipmentItemResponse, status_code=status.HTTP_201_CREATED)
async def add_equipment_item(
    donation_id: UUID,
    item_data: DonationEquipmentItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add equipment item to donation."""
    service = DonationService(db)

    # Verify donation exists
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    item = await service.add_equipment_item(
        donation_id,
        item_data,
        created_by=current_user.username
    )
    return item


@router.patch("/{donation_id}/equipment-items/{item_id}", response_model=DonationEquipmentItemResponse)
async def update_equipment_item(
    donation_id: UUID,
    item_id: UUID,
    item_data: DonationEquipmentItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update equipment item."""
    service = DonationService(db)

    item = await service.update_equipment_item(
        item_id,
        item_data,
        updated_by=current_user.username
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment item not found",
        )

    return item


@router.delete("/{donation_id}/equipment-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_item(
    donation_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete equipment item."""
    service = DonationService(db)

    success = await service.soft_delete_equipment_item(
        item_id,
        updated_by=current_user.username
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment item not found",
        )


# Medical Device Item Endpoints
@router.post("/{donation_id}/medical-device-items", response_model=DonationMedicalDeviceItemResponse, status_code=status.HTTP_201_CREATED)
async def add_medical_device_item(
    donation_id: UUID,
    item_data: DonationMedicalDeviceItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add medical device item to donation."""
    service = DonationService(db)

    # Verify donation exists
    donation = await service.get_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    item = await service.add_medical_device_item(
        donation_id,
        item_data,
        created_by=current_user.username
    )
    return item


@router.patch("/{donation_id}/medical-device-items/{item_id}", response_model=DonationMedicalDeviceItemResponse)
async def update_medical_device_item(
    donation_id: UUID,
    item_id: UUID,
    item_data: DonationMedicalDeviceItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update medical device item."""
    service = DonationService(db)

    item = await service.update_medical_device_item(
        item_id,
        item_data,
        updated_by=current_user.username
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device item not found",
        )

    return item


@router.delete("/{donation_id}/medical-device-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_device_item(
    donation_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete medical device item."""
    service = DonationService(db)

    success = await service.soft_delete_medical_device_item(
        item_id,
        updated_by=current_user.username
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical device item not found",
        )

