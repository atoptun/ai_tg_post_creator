from datetime import datetime, timezone
from typing import List

from faststream.rabbit import RabbitRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.repositories.keywords import KeywordRepository
from app.repositories.news_item import NewsItemRepository
from app.utils.logger import logger

logger = logger.getChild("filter")

router = RabbitRouter()
generate_publisher = router.publisher("generate-post-queue")

def _normalize_text(value: str | None) -> str:
    return (value or "").strip()

def _item_text(item: dict) -> str:
    return " ".join(
        _normalize_text(item.get(field)) for field in ("title", "summary", "raw_text")
    ).lower()

def _matches_keywords(item: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = _item_text(item)
    return any(keyword in text for keyword in keywords)

async def _load_keywords(db: AsyncSession) -> list[str]:
    keyword_repo = KeywordRepository(db)
    keywords = await keyword_repo.get_list()
    return [keyword.word.lower() for keyword in keywords]

@router.subscriber("filter-news-queue")
async def task_filter_news(items: List[dict]) -> None:
    """
    Filter raw news by keywords, save unique NewsItem rows, and enqueue
    generation by passing `news_id` to the next queue.
    """
    logger.info(f"Filter received batch of {len(items) if items else 0} items")

    if not items:
        return

    filtered_out = 0
    saved = 0

    async with AsyncSessionLocal() as db:
        keywords = await _load_keywords(db)
        news_repo = NewsItemRepository(db)

        for item in items:
            if not _matches_keywords(item, keywords):
                filtered_out += 1
                continue

            published_at = item.get("published_at")
            if isinstance(published_at, str):
                try:
                    if published_at.endswith("Z"):
                        published_at = published_at[:-1] + "+00:00"
                    item["published_at"] = datetime.fromisoformat(published_at)
                except Exception as ex:
                    logger.error(
                        f"Failed parsing published_at string '{published_at}': {ex}"
                    )
                    item["published_at"] = datetime.now(timezone.utc)

            try:
                news = await news_repo.create(**item)
            except IntegrityError:
                await db.rollback()
                logger.info(f"Duplicate news item skipped: {item.get('title')}")
                continue
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed inserting news item: {e}")
                continue

            saved += 1
            await generate_publisher.publish(message=news.id)
            logger.info(f"Enqueued generation for news id={news.id}")

    logger.info(
        f"Filter finished: saved={saved}, filtered_out={filtered_out}"
    )
