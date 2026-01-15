from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.medicine import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse,
    MedicineListResponse,
)
from app.services.medicine_service import MedicineService
from app.utils.database import get_db
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    medicine_data: MedicineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new medicine."""
    service = MedicineService(db)

    if medicine_data.code:
        existing = await service.get_by_code(medicine_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine code already exists",
            )

    if medicine_data.barcode:
        existing = await service.get_by_barcode(medicine_data.barcode)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode already registered",
            )

    return await service.create(medicine_data, created_by=current_user.username)


@router.get("/", response_model=MedicineListResponse)
async def list_medicines(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    category_id: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all medicines with pagination and filtering."""
    service = MedicineService(db)
    medicines, total = await service.list_medicines(
        page=page,
        size=size,
        category_id=category_id,
        is_active=is_active,
        search=search,
    )
    return MedicineListResponse(data=medicines, total=total, page=page, size=size)


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(
    medicine_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific medicine by ID."""
    service = MedicineService(db)
    medicine = await service.get_by_id(medicine_id)
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )
    return medicine


@router.patch("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: UUID,
    medicine_data: MedicineUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a medicine."""
    service = MedicineService(db)
    medicine = await service.get_by_id(medicine_id)
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    if medicine_data.code and medicine_data.code != medicine.code:
        existing = await service.get_by_code(medicine_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medicine code already exists",
            )

    if medicine_data.barcode and medicine_data.barcode != medicine.barcode:
        existing = await service.get_by_barcode(medicine_data.barcode)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode already registered",
            )

    return await service.update(medicine, medicine_data, updated_by=current_user.username)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(
    medicine_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a medicine."""
    service = MedicineService(db)
    medicine = await service.get_by_id(medicine_id)
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )
    await service.delete(medicine)

