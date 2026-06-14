from datetime import datetime, timezone

from faststream.rabbit import RabbitRouter

from app.db import AsyncSessionLocal
from app.repositories.post import PostRepository
from app.telegram.publisher import publish_post_to_telegram
from app.utils.logger import logger


logger = logger.getChild("telegram_publish_task")

router = RabbitRouter()
publish_publisher = router.publisher("publish-telegram-queue")


@router.subscriber("publish-telegram-queue")
async def handle_publish_post(post_id: int) -> None:
    """Send a generated post to Telegram and mark it published."""
    logger.info(f"Telegram publish request received for post_id={post_id}")

    async with AsyncSessionLocal() as db:
        post_repo = PostRepository(db)

        post = await post_repo.get_by_id(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return

        if post.status == "published":
            logger.info(f"Post {post_id} already published; skipping")
            return

        try:
            published = await publish_post_to_telegram(post.generated_text)
            if not published:
                await post_repo.update(post, status="failed")
                return

            await post_repo.update(
                post,
                status="published",
                published_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            logger.info(f"Post {post_id} published to Telegram")

        except Exception as e:
            logger.error(f"Failed to publish post {post_id} to Telegram: {e}")
            await post_repo.update(post, status="failed")
