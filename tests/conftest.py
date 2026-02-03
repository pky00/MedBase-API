"""Test configuration and fixtures."""
import asyncio
import pytest
import os
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Set test environment before importing app modules
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://medbase_test:medbase_test123@localhost:5433/medbase_test"
)

from app.utility.database import Base, get_db
from app.utility.security import get_password_hash
from app.model.user import User
from main import app


# Test database URL
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSessionLocal() as session:
        yield session
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        username="testadmin",
        email="testadmin@test.com",
        password_hash=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Create a regular user for testing."""
    user = User(
        username="testuser",
        email="testuser@test.com",
        password_hash=get_password_hash("testpass123"),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get JWT token for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    """Get JWT token for regular user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Get authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token: str) -> dict:
    """Get authorization headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}
