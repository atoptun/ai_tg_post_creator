from typing import Annotated
from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DbSessionDep
from app.models import NewsItem
from app.repositories.base import BaseRepository


class NewsItemRepository(BaseRepository[NewsItem]):
    """Repository handling specific data operations for the NewsItem model."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, NewsItem)

    async def get_sorted_paginated_list(
        self, params: Params | None = None,
        desc: bool = True
    ) -> Page[NewsItem]:
        """Returns a paginated list of news sorted by publication date descending."""
        sort_order = self.model.published_at.desc() if desc else self.model.published_at.asc()
        query = select(self.model).order_by(sort_order)
        return await apaginate(self.db, query, params=params)


async def get_news_item_repository(db: DbSessionDep) -> NewsItemRepository:
    return NewsItemRepository(db)


NewsItemRepoDep = Annotated[NewsItemRepository, Depends(get_news_item_repository)]
