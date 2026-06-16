from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from app.api.schemas import PostOut, QueueDispatchResponse
from app.tasks.telegram_publish import publish_publisher
from app.repositories.post import PostRepoDep


router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=Page[PostOut])
async def list_posts(
    post_repo: PostRepoDep,
    params: Params = Depends(),
):
    """
    Get a paginated list of all posts sorted by ID descending.
    """
    return await post_repo.get_paginated_posts(params=params)


@router.delete("/{post_id}", status_code=204)
async def delete_post(post_id: int, post_repo: PostRepoDep):
    """Delete a specific post."""
    post = await post_repo.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await post_repo.delete(post)


@router.get("/errors/", response_model=Page[PostOut])
async def list_failed_posts(
    post_repo: PostRepoDep,
    params: Params = Depends(),
):
    """
    Returns a paginated list of all posts that failed during generation or publishing.
    """
    return await post_repo.get_paginated_posts(params=params, status="failed")


@router.post(
    "/{post_id}/retry-publish",
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
