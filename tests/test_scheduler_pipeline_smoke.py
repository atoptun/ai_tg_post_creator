from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from faststream.rabbit import TestRabbitBroker
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Keyword, NewsItem, Post
from app.repositories.keywords import KeywordRepository
from app.scheduler_app import scheduled_parse_sites
from app.worker_app import broker
from app.tasks import filter, generator


@pytest.mark.asyncio
async def test_scheduler_batch_reaches_pipeline_and_routes_news_id(monkeypatch):
    """Smoke-test the scheduler output shape and the pipeline routing contract."""

    raw_items = [
        {
            "title": "AI beats benchmarks",
            "url": "https://example.com/ai",
            "summary": "AI news summary",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Details about AI progress",
        }
    ]

    published_messages: list[dict] = []

    async def fake_load_keywords(*args, **kwargs):
        return []

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    async def fake_create(self, **kwargs):
        return SimpleNamespace(id=1, **kwargs)

    async def fake_task_parse_sites(source_repo) -> AsyncIterator[list[dict]]:
        yield raw_items

    @asynccontextmanager
    async def fake_repo_context(repo_class, *args, **kwargs):
        yield SimpleNamespace()

    monkeypatch.setattr(filter, "_load_keywords", fake_load_keywords)
    monkeypatch.setattr(filter.generate_publisher, "publish", fake_publish)
    monkeypatch.setattr(filter.NewsItemRepository, "create", fake_create)
    monkeypatch.setattr("app.scheduler_app.task_parse_sites", fake_task_parse_sites)
    monkeypatch.setattr("app.scheduler_app.repo_context", fake_repo_context)

    batches = []
    async for batch in scheduled_parse_sites():
        batches.append(batch)

    assert batches == [raw_items]

    async with TestRabbitBroker(broker, with_real=False) as br:
        await br.publish(batches[0], "filter-news-queue")
        await filter.task_filter_news.wait_call(timeout=5)

    assert published_messages == [1]


@pytest.mark.asyncio
async def test_filter_news_queue_real_db_smoke_skips_non_matching_items(
    db_session, monkeypatch
):
    """Real-DB smoke test: broker delivery into the pipeline with keyword filtering and no mocks."""

    db_session.add(Keyword(word="ai"))
    await db_session.commit()

    @asynccontextmanager
    async def fake_session_local():
        yield db_session

    monkeypatch.setattr(filter, "AsyncSessionLocal", fake_session_local)

    async def fake_load_keywords(db, *args, **kwargs):
        keyword_repo = KeywordRepository(db)
        keywords = await keyword_repo.get_list()
        return [keyword.word.lower() for keyword in keywords]

    monkeypatch.setattr(filter, "_load_keywords", fake_load_keywords)

    raw_items = [
        {
            "title": "Sports update",
            "url": "https://example.com/sports",
            "summary": "Match recap",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "Football results",
        }
    ]

    await filter.task_filter_news(raw_items)

    news_count = await db_session.scalar(select(func.count()).select_from(NewsItem))

    assert news_count == 0


@pytest.mark.asyncio
async def test_filter_news_queue_real_db_smoke_persists_news_and_post(
    db_session, monkeypatch
):
    """Real-DB smoke test: keyword match stores a NewsItem and generates a Post without OpenAI."""

    db_session.add(Keyword(word="ai"))
    await db_session.commit()

    published_messages: list[dict] = []

    async def fake_generate_post_text(news_item):
        return f"Generated post for {news_item.title}"

    async def fake_publish(*, message: dict):
        published_messages.append(message)

    @asynccontextmanager
    async def real_session_local():
        engine = create_async_engine(settings.postgres_url, echo=False)
        session_factory = async_sessionmaker(
            engine, expire_on_commit=False, autoflush=False
        )
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
                await engine.dispose()

    monkeypatch.setattr(generator, "generate_post_text", fake_generate_post_text)
    monkeypatch.setattr(filter, "AsyncSessionLocal", real_session_local)
    monkeypatch.setattr(generator, "AsyncSessionLocal", real_session_local)
    monkeypatch.setattr(filter.generate_publisher, "publish", fake_publish)
    monkeypatch.setattr(generator.publish_publisher, "publish", fake_publish)

    raw_items = [
        {
            "title": "AI market expands",
            "url": "https://example.com/ai-market",
            "summary": "AI adoption grows",
            "source": "Example",
            "published_at": datetime.now(timezone.utc),
            "raw_text": "This article is about AI progress and market expansion.",
        }
    ]

    await filter.task_filter_news(raw_items)

    news_count = await db_session.scalar(select(func.count()).select_from(NewsItem))

    assert news_count == 1
    assert published_messages == [1]

    news_result = await db_session.execute(select(NewsItem))
    news_item = news_result.scalars().one()

    await generator.task_generate_post(news_item.id)

    post_count = await db_session.scalar(select(func.count()).select_from(Post))
    post_result = await db_session.execute(select(Post))
    post = post_result.scalars().one()

    assert news_item.title == "AI market expands"
    assert post.news_id == news_item.id
    assert post.generated_text == "Generated post for AI market expands"
    assert post.status == "generated"
