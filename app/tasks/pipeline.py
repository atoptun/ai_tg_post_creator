from typing import List

from faststream.rabbit import RabbitRouter
from sqlalchemy.exc import IntegrityError

from app.ai.generator import generate_post_text
from app.db import AsyncSessionLocal
from app.repositories.keywords import KeywordRepository
from app.repositories.news_item import NewsItemRepository
from app.repositories.post import PostRepository
from app.utils.logger import logger


logger = logger.getChild("pipeline")

router = RabbitRouter()

generate_publisher = router.publisher("generate-post-queue")
publish_publisher = router.publisher("publish-telegram-queue")


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


async def _load_keywords() -> list[str]:
    async with AsyncSessionLocal() as db:
        keyword_repo = KeywordRepository(db)
        keywords = await keyword_repo.get_list()
        return [keyword.word.lower() for keyword in keywords]


@router.subscriber("filter-news-queue")
async def handle_raw_items(items: List[dict]) -> None:
    """
    Filter raw items by keywords, save unique NewsItem rows, and enqueue
    generation by passing `news_id` to the next queue.
    """
    logger.info(f"Pipeline received batch of {len(items) if items else 0} items")

    if not items:
        return

    keywords = await _load_keywords()
    filtered_out = 0
    saved = 0

    async with AsyncSessionLocal() as db:
        news_repo = NewsItemRepository(db)

        for item in items:
            if not _matches_keywords(item, keywords):
                filtered_out += 1
                continue

            try:
                news = await news_repo.create(**item)
            except IntegrityError:
                logger.info(f"Duplicate news item skipped: {item.get('title')}")
                continue
            except Exception as e:
                logger.error(f"Failed inserting news item: {e}")
                continue

            saved += 1
            await generate_publisher.publish(message={"news_id": news.id})
            logger.info(f"Enqueued generation for news id={news.id}")

    logger.info(
        f"Pipeline finished: saved={saved}, filtered_out={filtered_out}, keywords={len(keywords)}"
    )


@router.subscriber("generate-post-queue")
async def handle_generate_post(news_id: int) -> None:
    """
    Generate a post for a saved NewsItem and persist the Post row.
    """
    logger.info(f"Generation request received for news_id={news_id}")

    async with AsyncSessionLocal() as db:
        post_repo = PostRepository(db)
        news_repo = NewsItemRepository(db)

        post = None
        try:
            news = await news_repo.get_by_id(news_id)
            if not news:
                logger.error(f"News {news_id} not found")
                return

            post = await post_repo.create(
                news_id=news.id, generated_text="", status="new"
            )
            generated_text = await generate_post_text(news)

            if not generated_text:
                await post_repo.update(post, status="failed")
                logger.error(f"Generation returned empty for news {news_id}")
                return

            await post_repo.update(
                post, generated_text=generated_text, status="generated"
            )
            logger.info(f"Post {post.id} generated successfully for news {news_id}")
            await publish_publisher.publish(message={"post_id": post.id})
            logger.info(f"Enqueued Telegram publish for post id={post.id}")

        except Exception as e:
            logger.error(f"Generation worker error for news {news_id}: {e}")
            try:
                if post is not None:
                    await post_repo.update(post, status="failed")
            except Exception:
                pass
