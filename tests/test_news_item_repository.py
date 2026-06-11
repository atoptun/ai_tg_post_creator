from datetime import datetime, timezone, timedelta
import pytest
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi_pagination import Params, pagination_ctx

from app.models import NewsItem
from app.repositories.news_item import NewsItemRepository


@pytest.mark.asyncio
async def test_create_news_item(db_session: AsyncSession, faker: Faker):
    """Ensure the repository successfully saves a news item using raw kwargs."""
    # Given
    repo = NewsItemRepository(db_session)
    news_data = {
        "title": faker.unique.sentence(),
        "url": faker.unique.url(),
        "summary": faker.paragraph(),
        "source": "TechCrunch",
        "published_at": datetime.now(timezone.utc),
        "raw_text": faker.text(),
    }

    # When
    saved_item = await repo.create(**news_data)

    # Then
    assert saved_item.id is not None
    assert saved_item.title == news_data["title"]
    assert saved_item.source == "TechCrunch"
    assert saved_item.url == news_data["url"]


@pytest.mark.asyncio
async def test_create_news_item_with_nullable_url(
    db_session: AsyncSession, faker: Faker
):
    """Ensure news item can be created with a None URL (nullable=True)."""
    # Given
    repo = NewsItemRepository(db_session)
    news_data = {
        "title": faker.unique.sentence(),
        "url": None,  # Testing nullable column
        "summary": None,
        "source": "Telegram Channel",
        "published_at": datetime.now(timezone.utc),
        "raw_text": None,
    }

    # When
    saved_item = await repo.create(**news_data)

    # Then
    assert saved_item.id is not None
    assert saved_item.url is None
    assert saved_item.summary is None


@pytest.mark.asyncio
async def test_create_news_item_duplicate_title_raises_error(
    db_session: AsyncSession, faker: Faker
):
    """Ensure database constraint triggers IntegrityError on duplicate titles."""
    # Given
    repo = NewsItemRepository(db_session)
    shared_title = "Breaking AI News Today"

    item_1_data = {
        "title": shared_title,
        "url": faker.unique.url(),
        "source": "Reuters",
        "published_at": datetime.now(timezone.utc),
    }
    await repo.create(**item_1_data)

    item_2_data = {
        "title": shared_title,  # Duplicate trigger
        "url": faker.unique.url(),
        "source": "BBC",
        "published_at": datetime.now(timezone.utc),
    }

    # When & Then
    with pytest.raises(IntegrityError):
        await repo.create(**item_2_data)


@pytest.mark.asyncio
async def test_update_news_item_partial(db_session: AsyncSession, faker: Faker):
    """Ensure partial update applies fields dynamically."""
    # Given
    repo = NewsItemRepository(db_session)
    initial_data = {
        "title": faker.unique.sentence(),
        "url": faker.unique.url(),
        "source": "Bloomberg",
        "published_at": datetime.now(timezone.utc),
        "summary": "Old Summary",
    }
    item = await repo.create(**initial_data)

    # When: Updating summary and title
    new_title = "Completely New Title"
    updated_item = await repo.update(item, title=new_title, summary="New Summary")

    # Then
    assert updated_item.title == new_title
    assert updated_item.summary == "New Summary"
    assert updated_item.source == "Bloomberg"  # Unchanged field remains intact


@pytest.mark.asyncio
async def test_update_news_item_ignores_none_on_non_nullable(
    db_session: AsyncSession, faker: Faker
):
    """Ensure defensive check inside BaseRepository protects non-nullable fields from None."""
    # Given
    repo = NewsItemRepository(db_session)
    initial_data = {
        "title": faker.unique.sentence(),
        "url": faker.unique.url(),
        "source": "NYT",
        "published_at": datetime.now(timezone.utc),
    }
    item = await repo.create(**initial_data)

    # When: Passing a dirty None to a non-nullable field (title)
    # and a valid None to a nullable field (url)
    updated_item = await repo.update(item, title=None, url=None)

    # Then
    assert updated_item.title is not None  # Protective continue statement worked!
    assert updated_item.title == initial_data["title"]  # Kept the old valid title
    assert updated_item.url is None  # Allowed because url is nullable=True


@pytest.mark.asyncio
async def test_get_paginated_news_items(db_session: AsyncSession, faker: Faker):
    """Ensure generic pagination works flawlessly for news items."""
    # Given
    repo = NewsItemRepository(db_session)

    # Seed 7 clean news items
    for _ in range(7):
        await repo.create(
            title=faker.unique.sentence(),
            url=faker.unique.url(),
            source=faker.company(),
            published_at=datetime.now(timezone.utc),
        )

    # When: Request page 1 with size 3
    from fastapi_pagination import Params

    page = await repo.get_paginated_list(params=Params(page=1, size=3))

    # Then
    assert page.total == 7
    assert page.page == 1
    assert page.size == 3
    assert len(page.items) == 3


@pytest.mark.asyncio
async def test_get_sorted_paginated_list_descending(
    db_session: AsyncSession, faker: Faker
):
    """Ensure news items are sorted by published_at in DESCENDING order (newest first)."""
    # Given
    repo = NewsItemRepository(db_session)
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Seed 3 items with distinct publication dates
    await repo.create(
        title="Oldest",
        url=faker.unique.url(),
        source="A",
        published_at=base_time - timedelta(days=2),
    )
    await repo.create(
        title="Newest", url=faker.unique.url(), source="B", published_at=base_time
    )
    await repo.create(
        title="Middle",
        url=faker.unique.url(),
        source="C",
        published_at=base_time - timedelta(days=1),
    )

    # When: Call with default desc=True
    test_params = Params(page=1, size=10)
    page = await repo.get_sorted_paginated_list(params=test_params, desc=True)

    # Then: Verify strict DESC order (Newest -> Middle -> Oldest)
    assert page.total == 3
    assert page.items[0].title == "Newest"
    assert page.items[1].title == "Middle"
    assert page.items[2].title == "Oldest"


@pytest.mark.asyncio
async def test_get_sorted_paginated_list_ascending(
    db_session: AsyncSession, faker: Faker
):
    """Ensure news items are sorted by published_at in ASCENDING order (oldest first)."""
    # Given
    repo = NewsItemRepository(db_session)
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Seed same 3 items
    await repo.create(
        title="Oldest",
        url=faker.unique.url(),
        source="A",
        published_at=base_time - timedelta(days=2),
    )
    await repo.create(
        title="Newest", url=faker.unique.url(), source="B", published_at=base_time
    )
    await repo.create(
        title="Middle",
        url=faker.unique.url(),
        source="C",
        published_at=base_time - timedelta(days=1),
    )

    # When: Call with explicit desc=False (Ascending order)
    test_params = Params(page=1, size=10)
    page = await repo.get_sorted_paginated_list(params=test_params, desc=False)

    # Then: Verify strict ASC order (Oldest -> Middle -> Newest)
    assert page.total == 3
    assert page.items[0].title == "Oldest"
    assert page.items[1].title == "Middle"
    assert page.items[2].title == "Newest"


@pytest.mark.asyncio
async def test_get_sorted_paginated_list_slices(db_session: AsyncSession, faker: Faker):
    """Ensure limit and offset parameters work cleanly with sorted query results."""
    # Given
    repo = NewsItemRepository(db_session)
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    for i in range(4):
        await repo.create(
            title=f"News {i}",
            url=faker.unique.url(),
            source=faker.company(),
            published_at=base_time - timedelta(hours=i),
        )

    # When: Request Page 2 with size 2 (with default desc=True, should return items index 2 and 3)
    test_params = Params(page=2, size=2)
    page = await repo.get_sorted_paginated_list(params=test_params, desc=True)

    # Then
    assert page.total == 4
    assert page.page == 2
    assert page.size == 2
    assert len(page.items) == 2
    assert page.items[0].title == "News 2"
    assert page.items[1].title == "News 3"
