import pytest
from httpx import AsyncClient
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Keyword


@pytest.mark.asyncio
async def test_api_create_keyword(client: AsyncClient):
    """Ensure POST /api/keywords/ successfully registers a new keyword."""
    # Given
    payload = {"word": "keyword"}

    # When
    response = await client.post("/api/keywords/", json=payload)

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["word"] == "keyword"


@pytest.mark.asyncio
async def test_api_get_keyword_by_id(client: AsyncClient, db_session: AsyncSession):
    """Ensure GET /api/keywords/{id} returns detailed keyword information."""
    # Given
    keyword = Keyword(word="keyword")
    db_session.add(keyword)
    await db_session.commit()

    # When
    response = await client.get(f"/api/keywords/{keyword.id}")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == keyword.id
    assert data["word"] == "keyword"


@pytest.mark.asyncio
async def test_api_get_keyword_not_found(client: AsyncClient):
    """Ensure GET /api/keywords/{id} returns 404 for a non-existent ID."""
    # When
    response = await client.get("/api/keywords/99999")

    # Then
    assert response.status_code == 404
    assert response.json()["detail"] == "Keyword not found"


@pytest.mark.asyncio
async def test_api_update_keyword(client: AsyncClient, db_session: AsyncSession):
    """Ensure PATCH /api/keywords/{id} not allowed."""
    # Given
    keyword = Keyword(word="old_keyword")
    db_session.add(keyword)
    await db_session.commit()

    payload = {"word": "new_keyword"}

    # When
    response = await client.patch(f"/api/keywords/{keyword.id}", json=payload)

    # Then
    assert response.status_code == 405
    assert response.json()["detail"] == "Method Not Allowed"


@pytest.mark.asyncio
async def test_api_delete_keyword(client: AsyncClient, db_session: AsyncSession):
    """Ensure DELETE /api/keywords/{id} removes the entity entirely."""
    # Given
    keyword = Keyword(word="To Delete keyword")
    db_session.add(keyword)
    await db_session.commit()

    # When
    response = await client.delete(f"/api/keywords/{keyword.id}")

    # Then
    assert response.status_code == 204

    # Extra check: ensure it's gone from the DB context
    check_response = await client.get(f"/api/keywords/{keyword.id}")
    assert check_response.status_code == 404


@pytest.mark.asyncio
async def test_api_list_keywords_pagination(
    client: AsyncClient, db_session: AsyncSession, faker: Faker
):
    """Ensure GET /api/keywords/ handles query-string pagination params and wraps into a Page schema."""
    # Given
    # Seed 15 unique keywords using faker
    keywords = [
        Keyword(word=faker.unique.word())
        for _ in range(15)
    ]
    db_session.add_all(keywords)
    await db_session.commit()

    # When: Request page 1 with size 5
    response = await client.get("/api/keywords/?page=1&size=5")

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
