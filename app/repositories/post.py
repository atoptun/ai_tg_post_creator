from typing import Annotated
from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import DbSessionDep
from app.models import Post
from app.repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    """Repository handling specific data operations for the Post model."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Post)

    async def get_paginated_posts(
        self, params: Params | None = None, status: str | None = None
    ) -> Page[Post]:
        """
        Returns a paginated list of posts sorted by ID descending.
        Optionally filters posts by their execution/publishing status.
        """
        query = select(self.model).order_by(self.model.id.desc())

        if status is not None:
            query = query.where(self.model.status == status)

        return await apaginate(self.db, query, params=params)


async def get_post_repository(db: DbSessionDep) -> PostRepository:
    return PostRepository(db)


PostRepoDep = Annotated[PostRepository, Depends(get_post_repository)]
