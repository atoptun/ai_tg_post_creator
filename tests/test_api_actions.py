from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.models import Keyword, NewsItem, Post, Source
from app.api.endpoints import news as news_endpoint
from app.api.endpoints import posts as posts_endpoint


@pytest.mark.asyncio
async def test_api_manual_generate_queues_news_id(
    client: AsyncClient, db_session, monkeypatch
):
    news = NewsItem(
        title="AI growth continues",
        url="https://example.com/news",
        summary="Summary",
        source="Example",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()

    published_messages: list[dict] = []

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    monkeypatch.setattr(news_endpoint.generate_publisher, "publish", fake_publish)

    response = await client.post(f"/api/news/{news.id}/generate")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["news_id"] == news.id
    assert published_messages == [{"news_id": news.id}]


@pytest.mark.asyncio
async def test_api_retry_publish_post_queues_post_id(
    client: AsyncClient, db_session, monkeypatch
):
    news = NewsItem(
        title="AI growth continues",
        url="https://example.com/news",
        summary="Summary",
        source="Example",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    post = Post(news_id=news.id, generated_text="Generated text", status="failed")
    db_session.add(post)
    await db_session.commit()

    published_messages: list[dict] = []

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    monkeypatch.setattr(posts_endpoint.publish_publisher, "publish", fake_publish)

    response = await client.post(f"/api/posts/{post.id}/retry-publish")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["post_id"] == post.id
    assert published_messages == [{"post_id": post.id}]


@pytest.mark.asyncio
async def test_api_monitoring_summary_returns_counts(client: AsyncClient, db_session):
    db_session.add_all(
        [
            Source(name="Site A", type="site", url="https://a.example", enabled=True),
            Source(name="Site B", type="tg", url="https://t.me/b", enabled=False),
            Keyword(word="ai"),
        ]
    )
    await db_session.commit()

    news = NewsItem(
        title="AI growth continues",
        url="https://example.com/news",
        summary="Summary",
        source="Example",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    db_session.add_all(
        [
            Post(news_id=news.id, generated_text="Text A", status="generated"),
            Post(news_id=news.id, generated_text="Text B", status="failed"),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["sources_total"] == 2
    assert data["sources_enabled"] == 1
    assert data["keywords_total"] == 1
    assert data["news_items_total"] == 1
    assert data["posts_total"] == 2
    assert data["posts_by_status"]["generated"] == 1
    assert data["posts_by_status"]["failed"] == 1
    assert len(data["recent_failed_posts"]) == 1
