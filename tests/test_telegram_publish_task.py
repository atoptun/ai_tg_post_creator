from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Post
from app.tasks import telegram_publish


@pytest.mark.asyncio
async def test_task_publish_post_marks_post_published(
    db_session: AsyncSession, monkeypatch
):
    """Telegram publish worker should send the post text and mark the row published."""

    news = NewsItem(
        title="AI market expands",
        url="https://example.com/news",
        summary="A short summary",
        source="Example",
        published_at=datetime.now(timezone.utc),
        raw_text="Full article text",
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    post = Post(
        news_id=news.id,
        generated_text="Generated Telegram post",
        status="generated",
    )
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    published_messages: list[str] = []

    async def fake_publish_post_to_telegram(message_text: str) -> bool:
        published_messages.append(message_text)
        return True

    @asynccontextmanager
    async def fake_session_local():
        yield db_session

    monkeypatch.setattr(
        telegram_publish, "publish_post_to_telegram", fake_publish_post_to_telegram
    )
    monkeypatch.setattr(telegram_publish, "AsyncSessionLocal", fake_session_local)

    await telegram_publish.task_publish_post(post.id)

    result = await db_session.execute(select(Post))
    saved_post = result.scalars().one()

    assert published_messages == ["Generated Telegram post"]
    assert saved_post.status == "published"
    assert saved_post.published_at is not None
