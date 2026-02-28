import asyncio
from logging.config import fileConfig
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load .env file
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models
from app.utility.database import Base
from app.model.third_party import ThirdParty  # noqa: F401
from app.model.user import User  # noqa: F401 - Import to register model
from app.model.medicine_category import MedicineCategory  # noqa: F401
from app.model.equipment_category import EquipmentCategory  # noqa: F401
from app.model.medical_device_category import MedicalDeviceCategory  # noqa: F401
from app.model.medicine import Medicine  # noqa: F401
from app.model.equipment import Equipment  # noqa: F401
from app.model.medical_device import MedicalDevice  # noqa: F401
from app.model.inventory import Inventory  # noqa: F401
from app.model.partner import Partner  # noqa: F401
from app.model.doctor import Doctor  # noqa: F401
from app.model.patient import Patient  # noqa: F401
from app.model.patient_document import PatientDocument  # noqa: F401
from app.model.appointment import Appointment  # noqa: F401
from app.model.vital_sign import VitalSign  # noqa: F401
from app.model.medical_record import MedicalRecord  # noqa: F401
from app.model.treatment import Treatment  # noqa: F401
from app.model.inventory_transaction import InventoryTransaction  # noqa: F401
from app.model.inventory_transaction_item import InventoryTransactionItem  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from environment variable
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
