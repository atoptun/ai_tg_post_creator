import pytest
from sqlalchemy import select
from fastapi_pagination import Page, Params
from sqlalchemy.ext.asyncio import AsyncSession
from faker import Faker

from app.models import Source
from app.api.schemas import SourceCreate, SourceUpdate
from app.repositories.source import SourceRepository


@pytest.mark.asyncio
async def test_seed_test_source_fixture(test_source: Source):
    """Ensure the shared test source fixture seeds a stable enabled site source."""
    assert test_source.id is not None
    assert test_source.name == "Test News Site"
    assert test_source.type == "site"
    assert test_source.url == "https://example.com"
    assert test_source.enabled is True


@pytest.mark.asyncio
async def test_create_source(db_session: AsyncSession):
    """Ensure the repository successfully creates and saves a source to the DB."""
    # Given
    repo = SourceRepository(db_session)
    source_data = SourceCreate(
        name="Backend Blog", type="site", url="https://backend.dev"
    )

    # When
    saved_source = await repo.create(**source_data.model_dump(exclude_unset=True))

    # Then
    assert saved_source.id is not None
    assert saved_source.name == "Backend Blog"
    assert saved_source.type == "site"
    assert saved_source.url == "https://backend.dev"

    # Extra verification: directly check the database record
    db_result = await db_session.execute(
        select(Source).where(Source.id == saved_source.id)
    )
    persisted_source = db_result.scalar_one_or_none()
    assert persisted_source is not None


@pytest.mark.asyncio
async def test_get_by_id(db_session: AsyncSession):
    """Ensure we can retrieve a specific source using its unique ID."""
    # Given
    repo = SourceRepository(db_session)
    existing_source = Source(
        name="Python Channel", type="tg", url="https://t.me/python"
    )
    db_session.add(existing_source)
    await db_session.commit()

    # When
    found_source = await repo.get_by_id(existing_source.id)

    # Then
    assert found_source is not None
    assert found_source.id == existing_source.id
    assert found_source.name == "Python Channel"


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session: AsyncSession):
    """Ensure the method returns None gracefully if the ID does not exist."""
    # Given
    repo = SourceRepository(db_session)

    # When
    found_source = await repo.get_by_id(9999)  # Non-existent ID

    # Then
    assert found_source is None


@pytest.mark.asyncio
async def test_get_paginated_list(db_session: AsyncSession):
    """Ensure fastapi-pagination correctly wraps the DB query into a Page object."""
    # Given
    repo = SourceRepository(db_session)
    # Seed multiple sources to verify list wrapping
    sources = [
        Source(name="Source 1", type="site", url="https://src1.com"),
        Source(name="Source 2", type="tg", url="https://t.me/src2"),
    ]
    db_session.add_all(sources)
    await db_session.commit()

    # When
    # Outside an HTTP request context, fastapi-pagination falls back to page=1, size=50
    test_params = Params(page=1, size=50)
    result: Page = await repo.get_paginated_list(params=test_params)

    # Then
    assert isinstance(result, Page)
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].name == "Source 1"
    assert result.items[1].name == "Source 2"


@pytest.mark.asyncio
async def test_update_source(db_session: AsyncSession):
    """Ensure partial updates correctly apply fields while leaving others intact."""
    # Given
    repo = SourceRepository(db_session)
    source = Source(name="Old Name", type="site", url="https://old.com")
    db_session.add(source)
    await db_session.commit()

    # Change name only, passing None for type to test 'exclude_none=True' logic
    update_data = SourceUpdate(name="New Awesome Name", type=None)

    # When
    updated_source = await repo.update(source, **update_data.model_dump())

    # Then
    assert updated_source.name == "New Awesome Name"
    assert updated_source.type == "site"


@pytest.mark.asyncio
async def test_delete_source(db_session: AsyncSession):
    """Ensure the target entity is completely removed from the database."""
    # Given
    repo = SourceRepository(db_session)
    source = Source(name="To Be Deleted", type="site", url="https://delete-me.com")
    db_session.add(source)
    await db_session.commit()

    # When
    await repo.delete(source)

    # Then
    # Double check that fetching the record returns None
    db_result = await db_session.execute(select(Source).where(Source.id == source.id))
    deleted_source = db_result.scalar_one_or_none()
    assert deleted_source is None


@pytest.mark.asyncio
async def test_get_paginated_list_multiple_pages(
    db_session: AsyncSession, faker: Faker
):
    """Ensure pagination parameters work correctly across multiple data pages."""
    # Given
    repo = SourceRepository(db_session)

    # Total items to generate (75 items = 3 full pages if page size is 25)
    total_items = 75
    page_size = 25

    # Generate 75 fake sources using Faker loops
    fake_sources = [
        Source(
            name=faker.company(),
            type=faker.random_element(elements=("site", "tg")),
            url=faker.unique.url(),
        )
        for _ in range(total_items)
    ]

    db_session.add_all(fake_sources)
    await db_session.commit()

    # --- Test Page 1 ---
    params_page_1 = Params(page=1, size=page_size)
    result_page_1: Page = await repo.get_paginated_list(params=params_page_1)

    assert result_page_1.total == total_items
    assert result_page_1.page == 1
    assert result_page_1.size == page_size
    assert len(result_page_1.items) == page_size

    # Save the first item's ID to ensure next pages don't duplicate it
    first_page_first_id = result_page_1.items[0].id

    # --- Test Page 2 ---
    params_page_2 = Params(page=2, size=page_size)
    result_page_2: Page = await repo.get_paginated_list(params=params_page_2)

    assert result_page_2.page == 2
    assert len(result_page_2.items) == page_size
    # Ensure items on page 2 are different from page 1
    assert result_page_2.items[0].id != first_page_first_id

    # --- Test Page 3 (The Last Page) ---
    params_page_3 = Params(page=3, size=page_size)
    result_page_3: Page = await repo.get_paginated_list(params=params_page_3)

    assert result_page_3.page == 3
    assert len(result_page_3.items) == page_size

    # --- Test Page 4 (Out of bounds / Empty page) ---
    params_page_4 = Params(page=4, size=page_size)
    result_page_4: Page = await repo.get_paginated_list(params=params_page_4)

    assert result_page_4.page == 4
    assert len(result_page_4.items) == 0  # No more data left
