from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Post
from app.tasks import pipeline


@pytest.mark.asyncio
async def test_handle_raw_items_filters_keywords_and_enqueues_news_id(
    db_session: AsyncSession, monkeypatch
):
    """Only keyword-matching items should be stored and forwarded."""

    published_messages: list[dict] = []

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    async def fake_load_keywords():
        return ["ai"]

    monkeypatch.setattr(pipeline, "_load_keywords", fake_load_keywords)
    monkeypatch.setattr(pipeline.generate_publisher, "publish", fake_publish)

    items = [
        {
            "title": "AI beats benchmarks",
            "url": "https://example.com/ai",
            "summary": "AI news summary",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Details about AI progress",
        },
        {
            "title": "Sports update",
            "url": "https://example.com/sports",
            "summary": "Match recap",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Football results",
        },
        {
            "title": "AI beats benchmarks",
            "url": "https://example.com/ai",
            "summary": "AI news summary",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Details about AI progress",
        },
    ]

    await pipeline.handle_raw_items(items)

    result = await db_session.execute(select(NewsItem))
    saved_news = result.scalars().all()

    assert len(saved_news) == 1
    assert saved_news[0].title == "AI beats benchmarks"
    assert published_messages == [{"news_id": saved_news[0].id}]


@pytest.mark.asyncio
async def test_handle_raw_items_skips_duplicate_integrity_error(monkeypatch):
    """Duplicate items should be skipped without enqueueing a second time."""

    published_messages: list[dict] = []
    created_titles: list[str] = []

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    async def fake_load_keywords():
        return []

    async def fake_create(self, **kwargs):
        title = kwargs["title"]
        if title in created_titles:
            raise IntegrityError("insert news_items", kwargs, Exception("duplicate"))
        created_titles.append(title)
        return SimpleNamespace(id=len(created_titles), **kwargs)

    monkeypatch.setattr(pipeline, "_load_keywords", fake_load_keywords)
    monkeypatch.setattr(pipeline.generate_publisher, "publish", fake_publish)
    monkeypatch.setattr(pipeline.NewsItemRepository, "create", fake_create)

    items = [
        {
            "title": "AI beats benchmarks",
            "url": "https://example.com/ai",
            "summary": "AI news summary",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Details about AI progress",
        },
        {
            "title": "AI beats benchmarks",
            "url": "https://example.com/ai-duplicate",
            "summary": "Duplicate AI news summary",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Duplicate details about AI progress",
        },
    ]

    await pipeline.handle_raw_items(items)

    assert created_titles == ["AI beats benchmarks"]
    assert published_messages == [{"news_id": 1}]


@pytest.mark.asyncio
async def test_handle_generate_post_creates_generated_post(monkeypatch):
    """Generation worker should create a post and mark it as generated."""

    fake_news = SimpleNamespace(
        id=42,
        title="AI market expands",
        url="https://example.com/news",
        summary="A short summary",
        raw_text="Full article text",
    )
    created_posts: list[SimpleNamespace] = []
    updates: list[dict] = []
    published_messages: list[dict] = []

    async def fake_get_by_id(self, news_id: int):
        assert news_id == fake_news.id
        return fake_news

    async def fake_create(self, **kwargs):
        post = SimpleNamespace(id=1, **kwargs)
        created_posts.append(post)
        return post

    async def fake_update(self, db_obj, **kwargs):
        updates.append(kwargs)
        for field, value in kwargs.items():
            setattr(db_obj, field, value)
        return db_obj

    async def fake_generate_post_text(news_item):
        assert news_item is fake_news
        return "Generated Telegram post"

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    monkeypatch.setattr(pipeline.NewsItemRepository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(pipeline.PostRepository, "create", fake_create)
    monkeypatch.setattr(pipeline.PostRepository, "update", fake_update)
    monkeypatch.setattr(pipeline, "generate_post_text", fake_generate_post_text)
    monkeypatch.setattr(pipeline.publish_publisher, "publish", fake_publish)

    await pipeline.handle_generate_post(fake_news.id)

    assert len(created_posts) == 1
    assert created_posts[0].news_id == fake_news.id
    assert created_posts[0].generated_text == "Generated Telegram post"
    assert created_posts[0].status == "generated"
    assert updates == [
        {"generated_text": "Generated Telegram post", "status": "generated"}
    ]
    assert published_messages == [{"post_id": 1}]
