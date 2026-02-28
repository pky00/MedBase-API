"""Reset database: drop and recreate from DATABASE_URL."""
import asyncio
import sys
import os
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from app.utility.config import settings


async def reset_database():
    """Drop and recreate the database."""
    parsed = urlparse(settings.DATABASE_URL)
    db_name = parsed.path.lstrip("/")

    # Connect to default 'postgres' database to drop/create
    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database="postgres",
    )

    # Terminate existing connections
    await conn.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{db_name}'
        AND pid <> pg_backend_pid();
    """)

    await conn.execute(f"DROP DATABASE IF EXISTS {db_name};")
    print(f"Dropped database '{db_name}'.")

    await conn.execute(f"CREATE DATABASE {db_name};")
    print(f"Created database '{db_name}'.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(reset_database())
