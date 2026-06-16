import pytest
from httpx import AsyncClient
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Source


@pytest.mark.asyncio
async def test_api_create_source(client: AsyncClient):
    """Ensure POST /api/sources/ successfully registers a new source."""
    # Given
    payload = {"name": "API Test Blog", "type": "site", "url": "https://api-test.com"}

    # When
    response = await client.post("/api/sources/", json=payload)

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "API Test Blog"
    assert data["type"] == "site"
    assert data["url"] == "https://api-test.com"


@pytest.mark.asyncio
async def test_api_get_source_by_id(client: AsyncClient, db_session: AsyncSession):
    """Ensure GET /api/sources/{id} returns detailed source information."""
    # Given
    source = Source(name="Telegram Tech", type="tg", url="https://t.me/tech")
    db_session.add(source)
    await db_session.commit()

    # When
    response = await client.get(f"/api/sources/{source.id}")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == source.id
    assert data["name"] == "Telegram Tech"


@pytest.mark.asyncio
async def test_api_get_source_not_found(client: AsyncClient):
    """Ensure GET /api/sources/{id} returns 404 for a non-existent ID."""
    # When
    response = await client.get("/api/sources/99999")

    # Then
    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


@pytest.mark.asyncio
async def test_api_update_source(client: AsyncClient, db_session: AsyncSession):
    """Ensure PATCH /api/sources/{id} partially modifies fields."""
    # Given
    source = Source(name="Old API Name", type="site", url="https://old-api.com")
    db_session.add(source)
    await db_session.commit()

    payload = {"name": "New API Name"}

    # When
    response = await client.patch(f"/api/sources/{source.id}", json=payload)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New API Name"
    assert data["url"] == "https://old-api.com"  # Left intact


@pytest.mark.asyncio
async def test_api_delete_source(client: AsyncClient, db_session: AsyncSession):
    """Ensure DELETE /api/sources/{id} removes the entity entirely."""
    # Given
    source = Source(name="To Delete API", type="site", url="https://delete-api.com")
    db_session.add(source)
    await db_session.commit()

    # When
    response = await client.delete(f"/api/sources/{source.id}")

    # Then
    assert response.status_code == 204

    # Extra check: ensure it's gone from the DB context
    check_response = await client.get(f"/api/sources/{source.id}")
    assert check_response.status_code == 404


@pytest.mark.asyncio
async def test_api_list_sources_pagination(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure GET /api/sources/ handles query-string pagination params and wraps into a Page schema."""
    # Given
    # Seed 15 unique sources using faker
    sources = [
        Source(name=faker.company(), type="site", url=faker.unique.url())
        for _ in range(15)
    ]
    db_session.add_all(sources)
    await db_session.commit()

    # When: Request page 1 with size 5
    response = await client.get("/api/sources/?page=1&size=5")

    # Then
    assert response.status_code == 200
    data = response.json()

    # fastapi-pagination standard structure assertions
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data

    assert data["total"] == 15
    assert data["page"] == 1
    assert data["size"] == 5
    assert len(data["items"]) == 5
