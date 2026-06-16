from fastapi import APIRouter, Query, HTTPException

from app.repositories.post import PostRepoDep
from app.tasks.parsers import run_parser_publisher
from app.tasks.filter import generate_publisher
from app.tasks.telegram_publish import publish_publisher
from app.api.schemas import QueueDispatchResponse
from app.repositories.news_item import NewsItemRepoDep

router = APIRouter(prefix="/trigger", tags=["Triggers"])


@router.post("/run-parser", response_model=QueueDispatchResponse, status_code=202)
async def run_parser(
    source: str = Query(..., description="The parser source to run: 'site' or 'tg'"),
):
    """
    Manually trigger a parser run for the specified source ('site' or 'tg').
    """
    if source not in ("site", "tg", "telegram", "sites"):
        raise HTTPException(
            status_code=400, detail="Invalid source. Must be 'site' or 'tg'"
        )

    normalized_source = "tg" if source in ("tg", "telegram") else "site"

    await run_parser_publisher.publish(normalized_source)

    return QueueDispatchResponse(
        status="queued",
        message=f"Run parser event published for source: {normalized_source}",
    )


@router.post("/repost/{news_id}", response_model=QueueDispatchResponse, status_code=202)
async def manual_repost(news_id: int, news_repo: NewsItemRepoDep):
    """Manually enqueue a news item for reposting."""
    news = await news_repo.get_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    await generate_publisher.publish(message=news_id)
    return QueueDispatchResponse(status="queued", news_id=news_id)


@router.post(
    "/republish/{post_id}",
    response_model=QueueDispatchResponse,
    status_code=202,
)
async def retry_publish_post(post_id: int, post_repo: PostRepoDep):
    """Requeue a post for Telegram publication by post_id."""
    post = await post_repo.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await publish_publisher.publish(message=post_id)
    return QueueDispatchResponse(status="queued", post_id=post_id)
