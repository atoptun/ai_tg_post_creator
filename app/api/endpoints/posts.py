from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from app.api.schemas import PostOut
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


@router.get("/errors/", response_model=Page[PostOut])
async def list_failed_posts(
    post_repo: PostRepoDep,
    params: Params = Depends(),
):
    """
    Returns a paginated list of all posts that failed during generation or publishing.
    """
    return await post_repo.get_paginated_posts(params=params, status="failed")
