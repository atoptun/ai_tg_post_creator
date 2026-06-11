import pytest
import pytest_asyncio
from collections.abc import AsyncIterator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db import Base
from app.config import settings


# System engine for database management (creating/dropping test DB)
SYSTEM_DB_URL = settings.postgres_url.rsplit("/", 1)[0] + "/postgres"
system_engine = create_async_engine(SYSTEM_DB_URL, isolation_level="AUTOCOMMIT")

# Test engine and session for running tests against the test database
test_engine = create_async_engine(settings.postgres_url, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, autoflush=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def manage_test_database():
    """Automatically creates the test database before tests and optionally drops it after all tests."""
    test_db_name = settings.POSTGRES_DB

    async with system_engine.connect() as conn:
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'")
        )
        exists = result.scalar()

        if not exists:
            await conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    yield

    # Optional cleanup: Uncomment the following lines to drop the test database after all tests are done.
    # async with system_engine.connect() as conn:
    #     await conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name} WITH (FORCE)"))


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Creates tables before each test and clears them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provides a fresh database session for each test function, ensuring isolation and proper cleanup."""
    async with TestSessionLocal() as session:
        yield session
