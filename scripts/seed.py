"""Seed script to create initial admin user."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.utility.database import AsyncSessionLocal
from app.service.user import UserService
from app.schema.user import UserCreate


async def seed_admin():
    """Create initial admin user if it doesn't exist."""
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        
        # Check if admin already exists
        existing = await user_service.get_by_username("admin")
        if existing:
            print("Admin user already exists.")
            return
        
        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="admin@medbase.com",
            password="admin123",  # Change in production!
            role="admin",
            is_active=True
        )
        
        admin = await user_service.create(admin_data)
        await db.commit()
        
        print(f"Admin user created successfully!")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print("\nIMPORTANT: Change the default password in production!")


if __name__ == "__main__":
    asyncio.run(seed_admin())
