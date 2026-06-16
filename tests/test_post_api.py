from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, NewsItem


async def create_test_news_item(db_session: AsyncSession, faker: Faker) -> NewsItem:
    """Helper to seed a news item for foreign key compliance."""
    news = NewsItem(
        title=faker.unique.sentence(),
        url=faker.unique.url(),
        source="Telegram Channel",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)
    return news


@pytest.mark.asyncio
async def test_api_list_posts_empty(client: AsyncClient):
    """Ensure GET /api/posts/ returns empty pagination structure on empty database."""
    response = await client.get("/api/posts/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_api_list_posts_ordering_and_slices(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure GET /api/posts/ returns items ordered by ID DESC and respects pagination size."""
    news = await create_test_news_item(db_session, faker)

    # Seed 3 posts
    post_1 = Post(news_id=news.id, generated_text="First Post Text", status="new")
    post_2 = Post(news_id=news.id, generated_text="Second Post Text", status="new")
    post_3 = Post(news_id=news.id, generated_text="Third Post Text", status="new")

    db_session.add_all([post_1, post_2, post_3])
    await db_session.commit()

    # Request first page with size 2
    response = await client.get("/api/posts/?page=1&size=2")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    # Check strict descending ordering by ID (last created comes first)
    assert data["items"][0]["id"] > data["items"][1]["id"]


@pytest.mark.asyncio
async def test_api_list_failed_posts_isolation(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure GET /api/posts/errors/ isolates only posts with status='failed'."""
    news = await create_test_news_item(db_session, faker)

    # Seed mixed statuses
    db_session.add_all(
        [
            Post(news_id=news.id, generated_text="Successful post", status="published"),
            Post(
                news_id=news.id, generated_text="Crashed post text", status="failed"
            ),  # Target
            Post(news_id=news.id, generated_text="Pending post", status="generated"),
        ]
    )
    await db_session.commit()

    # Request errors endpoint
    response = await client.get("/api/posts/errors/?page=1&size=10")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "failed"
    assert data["items"][0]["generated_text"] == "Crashed post text"
