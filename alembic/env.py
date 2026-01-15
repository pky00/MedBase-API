import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Import your models and config
from app.utils.database import Base
from app.models import (
    User,
    Doctor,
    Patient,
    PatientAllergy,
    PatientMedicalHistory,
    Donor,
    MedicineCategory,
    Medicine,
    MedicineInventory,
    MedicineExpiry,
    EquipmentCategory,
    Equipment,
    MedicalDeviceCategory,
    MedicalDevice,
    MedicalDeviceInventory,
    Appointment,
    VitalSign,
    MedicalRecord,
    Donation,
    DonationMedicineItem,
    DonationEquipmentItem,
    DonationMedicalDeviceItem,
    Prescription,
    PrescriptionItem,
    PrescribedDevice,
    PatientDocument,
    InventoryTransaction,
    SystemSetting,
)
from app.config import get_settings

# this is the Alembic Config object
config = context.config

# Get settings
settings = get_settings()

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use sync URL for offline mode
    url = settings.database_url.replace("+asyncpg", "+psycopg2")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Use the async URL directly
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
