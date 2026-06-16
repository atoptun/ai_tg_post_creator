from faststream.rabbit import RabbitRouter

from app.ai.generator import generate_post_text
from app.db import AsyncSessionLocal
from app.repositories.news_item import NewsItemRepository
from app.repositories.post import PostRepository
from app.utils.logger import logger

logger = logger.getChild("generator")

router = RabbitRouter()
publish_publisher = router.publisher("publish-telegram-queue")

@router.subscriber("generate-post-queue")
async def task_generate_post(news_id: int) -> None:
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

            generated_text = await generate_post_text(news)

            post = await post_repo.create(
                news_id=news.id, generated_text=generated_text, status="generated"
            )
            logger.info(f"Post {post.id} generated successfully for news {news_id}")

            await publish_publisher.publish(message=post.id)
            logger.info(f"Enqueued Telegram publish for post id={post.id}")

        except Exception as e:
            logger.error(f"Generation worker error for news {news_id}: {e}")
            try:
                if post is not None:
                    await post_repo.update(post, status="failed")
            except Exception:
                pass
