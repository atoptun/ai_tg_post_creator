from datetime import datetime, timezone
import pytest
from faker import Faker
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, NewsItem
from app.repositories.post import PostRepository


async def create_test_news_item(db_session: AsyncSession, faker: Faker) -> NewsItem:
    """Helper utility to create a parent NewsItem for ForeignKey constraints."""
    news = NewsItem(
        title=faker.unique.sentence(),
        url=faker.unique.url(),
        source="TechCrunch",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)
    return news


@pytest.mark.asyncio
async def test_get_paginated_posts_ordering(db_session: AsyncSession, faker: Faker):
    """Ensure posts are strictly sorted by ID in descending order (newest first)."""
    # Given
    repo = PostRepository(db_session)
    news = await create_test_news_item(db_session, faker)

    for _ in range(3):
        db_session.add(Post(news_id=news.id, generated_text=faker.text(), status="new"))
    await db_session.commit()

    # When
    test_params = Params(page=1, size=10)
    page = await repo.get_paginated_posts(params=test_params)

    # Then: ID 3 must be first, ID 1 must be last (DESC order)
    assert page.total == 3
    assert len(page.items) == 3
    assert page.items[0].id > page.items[1].id
    assert page.items[1].id > page.items[2].id


@pytest.mark.asyncio
async def test_get_paginated_posts_filter_by_status(
    db_session: AsyncSession, faker: Faker
):
    """Ensure passing status='failed' safely isolates only broken post executions."""
    # Given
    repo = PostRepository(db_session)
    news = await create_test_news_item(db_session, faker)

    # Seed various posts with different statuses
    db_session.add_all(
        [
            Post(news_id=news.id, generated_text=faker.text(), status="published"),
            Post(news_id=news.id, generated_text=faker.text(), status="generated"),
            Post(
                news_id=news.id,
                generated_text="This execution crashed",
                status="failed",
            ),
        ]
    )
    await db_session.commit()

    # When
    test_params = Params(page=1, size=10)
    failed_page = await repo.get_paginated_posts(params=test_params, status="failed")
    all_page = await repo.get_paginated_posts(params=test_params)

    # Then
    assert all_page.total == 3

    assert failed_page.total == 1
    assert len(failed_page.items) == 1
    assert failed_page.items[0].status == "failed"
    assert failed_page.items[0].generated_text == "This execution crashed"


@pytest.mark.asyncio
async def test_get_paginated_posts_empty_result(db_session: AsyncSession):
    """Ensure the repo returns a clean empty page payload when table has no matching logs."""
    # Given
    repo = PostRepository(db_session)

    # When
    test_params = Params(page=1, size=5)
    page = await repo.get_paginated_posts(params=test_params, status="failed")

    # Then
    assert page.total == 0
    assert page.items == []
