from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from app.api.schemas import NewsItemOut
from app.repositories.news_item import NewsItemRepoDep


router = APIRouter(prefix="/news", tags=["News"])


@router.get("/", response_model=Page[NewsItemOut])
async def list_news(
    news_repo: NewsItemRepoDep,
    params: Params = Depends(),
):
    """
    Get a paginated list of news items.
    By default, it uses desc=True to return the freshest news on top.
    """
    return await news_repo.get_sorted_paginated_list(params=params, desc=True)


@router.delete("/{news_id}", status_code=204)
async def delete_news(news_id: int, news_repo: NewsItemRepoDep):
    """
    Delete a specific news item from the database registry by its ID.
    """
    news = await news_repo.get_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    await news_repo.delete(news)

