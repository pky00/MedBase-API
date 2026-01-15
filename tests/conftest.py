import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import subprocess
import sys
import os
import uuid

from app.main import app
from app.utils.database import Base, get_db
from app.models.user import User
from app.utils.security import get_password_hash


# Test database configuration
TEST_DB_HOST = "localhost"
TEST_DB_PORT = "5432"
TEST_DB_USER = "postgres"
TEST_DB_PASSWORD = "postgres"
TEST_DB_NAME = "medbase_clinic_test"

TEST_DATABASE_URL = f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"


def create_test_database():
    """Create test database if it doesn't exist, then drop all tables."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Connect to default postgres database to create test db
    conn = psycopg2.connect(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating test database: {TEST_DB_NAME}")
        cursor.execute(f'CREATE DATABASE {TEST_DB_NAME}')
    
    cursor.close()
    conn.close()
    
    # Connect to test database and drop all tables
    conn = psycopg2.connect(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        database=TEST_DB_NAME
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Drop all tables and types (enums)
    cursor.execute("""
        DO $$ DECLARE
            r RECORD;
        BEGIN
            -- Drop all tables
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
            -- Drop all enum types
            FOR r IN (SELECT typname FROM pg_type WHERE typcategory = 'E' AND typnamespace = 'public'::regnamespace) LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    
    cursor.close()
    conn.close()


def run_migrations():
    """Run Alembic migrations on test database."""
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        raise Exception(f"Failed to run migrations: {result.stderr}")
    
    print("Migrations applied successfully")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database before all tests."""
    print("\n" + "="*60)
    print("Setting up test database...")
    print("="*60)
    
    create_test_database()
    run_migrations()
    
    print("="*60)
    print("Test database ready!")
    print("="*60 + "\n")
    
    yield
    
    # Don't clean up - leave database as-is for inspection
    print("\n" + "="*60)
    print("Tests complete. Database left as-is for inspection.")
    print(f"Database: {TEST_DB_NAME}")
    print("="*60 + "\n")


# Create test engine with NullPool to avoid connection sharing issues
test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    poolclass=NullPool,  # No connection pooling for tests
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for querying/verifying database state."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client that uses the test database."""
    # Override get_db to use test database
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user via API and return user data with password."""
    # Generate unique username for this test
    unique_id = uuid.uuid4().hex[:8]
    
    # First login as admin to create the test user
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
    )
    
    if login_response.status_code != 200:
        pytest.fail(f"Failed to login as admin: {login_response.text}")
    
    admin_token = login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create test user with unique username
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@medbase.example",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
    }
    
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers=admin_headers,
    )
    
    if create_response.status_code != 201:
        pytest.fail(f"Failed to create test user: {create_response.text}")
    
    user_info = create_response.json()
    user_info["password"] = user_data["password"]
    return user_info


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: dict) -> dict:
    """Get authentication headers for the test user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    
    if response.status_code != 200:
        pytest.fail(f"Failed to login as test user: {response.text}")
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict:
    """Get authentication headers for the admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
    )
    
    if response.status_code != 200:
        pytest.fail(f"Failed to login as admin: {response.text}")
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
