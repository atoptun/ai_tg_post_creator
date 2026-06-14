import pytest
import pytest_asyncio
from collections.abc import AsyncIterator
from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.db import Base
from app.config import settings
from app.main import app
from app.db import get_db
from app.seed import seed_test_source


@pytest.fixture(scope="session")
def faker() -> Faker:
    """Provides a global Faker instance for generating fake test data."""
    return Faker()


@pytest_asyncio.fixture(scope="function")
async def test_engine_setup():
    """
    Provides a function-scoped engine cleanly tied to the current test's event loop.
    This guarantees asyncpg connection pools work flawlessly alongside FastStream loops.
    """
    # 1. Manage database existence (Fast, light check)
    system_db_url = settings.postgres_url.rsplit("/", 1)[0] + "/postgres"
    system_engine = create_async_engine(system_db_url, isolation_level="AUTOCOMMIT")
    test_db_name = settings.POSTGRES_DB

    async with system_engine.connect() as conn:
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{test_db_name}'")
        )
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    await system_engine.dispose()

    # 2. Yield an engine properly bound to the active loop of the running test
    engine = create_async_engine(settings.postgres_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db(test_engine_setup):
    """Creates database tables before EACH test and clears them after, ensuring loop safety."""
    async with test_engine_setup.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine_setup.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine_setup) -> AsyncIterator[AsyncSession]:
    """Provides a fresh database session for each test function with rollback safety."""
    session_factory = async_sessionmaker(
        test_engine_setup, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_source(db_session: AsyncSession):
    """Provide a stable enabled site source for tests that need scheduler input."""
    return await seed_test_source(db_session)


# API


@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncIterator[AsyncClient]:
    """
    Provides an async HTTP client for API integration tests.
    Overrides the database session dependency to use the isolated test database transaction.
    """
    # Override FastAPI dependency to use our isolated test db_session
    app.dependency_overrides[get_db] = lambda: db_session

    # Initialize the async client using ASGITransport for internal routing
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    # Clean up overrides after each test function finishes
    app.dependency_overrides.clear()
