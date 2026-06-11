from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import NewsItem


@pytest.mark.asyncio
async def test_api_list_news_empty(client: AsyncClient):
    """Ensure GET /api/news/ returns an empty paginated structure when no data exists."""
    # When
    response = await client.get("/api/news/")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["items"] == []


@pytest.mark.asyncio
async def test_api_list_news_pagination_and_sorting(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure GET /api/news/ strictly sorts items by publication date DESC and respects sizing."""
    # Given: Create 3 news items with explicit, sequential timestamps
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    old_news = NewsItem(
        title="Old News Item",
        url=faker.unique.url(),
        source="Reuters",
        published_at=base_time - timedelta(days=2),
    )
    new_news = NewsItem(
        title="Fresh News Item",
        url=faker.unique.url(),
        source="TechCrunch",
        published_at=base_time,
    )
    mid_news = NewsItem(
        title="Middle News Item",
        url=faker.unique.url(),
        source="BBC",
        published_at=base_time - timedelta(days=1),
    )

    db_session.add_all([old_news, new_news, mid_news])
    await db_session.commit()

    # When: Request page 1 with page size of 2
    response = await client.get("/api/news/?page=1&size=2")

    # Then: HTTP Layer assertions
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2

    # Check strict descending sort order: Newest (Fresh) -> Middle
    assert data["items"][0]["title"] == "Fresh News Item"
    assert data["items"][1]["title"] == "Middle News Item"


@pytest.mark.asyncio
async def test_api_delete_news_success(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure DELETE /api/news/{id} drops the entity and returns a 204 status."""
    # Given: Seed a single news item
    news = NewsItem(
        title="Target to Delete",
        url=faker.unique.url(),
        source="Bloomberg",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()

    # When: Send DELETE request
    response = await client.delete(f"/api/news/{news.id}")

    # Then
    assert response.status_code == 204

    # Verify deletion from DB
    response = await client.delete(f"/api/news/{news.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_delete_news_not_found(client: AsyncClient):
    """Ensure DELETE /api/news/{id} returns a 404 error if the record does not exist."""
    # When
    response = await client.delete("/api/news/999999")

    # Then
    assert response.status_code == 404
    assert response.json()["detail"] == "News not found"
