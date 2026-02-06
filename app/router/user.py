from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.utility.database import get_db
from app.utility.auth import get_current_admin_user
from app.service.user import UserService
from app.schema.user import UserCreate, UserUpdate, UserResponse
from app.schema.base import PaginatedResponse, MessageResponse
from app.model.user import User


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    role: Optional[str] = Query(None, description="Filter by role (admin/user)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in username and email"),
    sort: str = Query("id", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all users with pagination, filtering, and sorting.
    
    **Admin only.**
    
    - **page**: Page number (starts at 1)
    - **size**: Number of items per page (max 100)
    - **role**: Filter by role (admin/user)
    - **is_active**: Filter by active status
    - **search**: Search in username and email
    - **sort**: Field to sort by
    - **order**: Sort order (asc/desc)
    """
    user_service = UserService(db)
    users, total = await user_service.get_all(
        page=page,
        size=size,
        role=role,
        is_active=is_active,
        search=search,
        sort=sort,
        order=order
    )
    
    pages = (total + size - 1) // size  # Ceiling division
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get user by ID.
    
    **Admin only.**
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new user.
    
    **Admin only.**
    
    - **username**: Unique username (3-50 characters)
    - **email**: Unique email address
    - **password**: Password (minimum 6 characters)
    - **role**: User role (admin/user)
    - **is_active**: Account active status
    """
    user_service = UserService(db)
    
    # Check if username already exists
    existing = await user_service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing = await user_service.get_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await user_service.create(user_data, created_by=current_user.id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update an existing user.
    
    **Admin only.**
    
    All fields are optional. Only provided fields will be updated.
    """
    user_service = UserService(db)
    
    # Check if user exists
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check username uniqueness if being updated
    if user_data.username and user_data.username != user.username:
        existing = await user_service.get_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    # Check email uniqueness if being updated
    if user_data.email and user_data.email != user.email:
        existing = await user_service.get_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    updated_user = await user_service.update(
        user_id, user_data, updated_by=current_user.id
    )
    return updated_user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a user (soft delete).
    
    **Admin only.**
    
    Admin cannot delete themselves.
    """
    # Admin cannot delete themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete themselves"
        )
    
    user_service = UserService(db)
    
    # Check if user exists
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_service.delete(user_id, deleted_by=current_user.id)
    return MessageResponse(message="User deleted successfully")
