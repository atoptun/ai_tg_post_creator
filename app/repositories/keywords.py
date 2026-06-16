from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DbSessionDep
from app.models import Keyword
from app.repositories.base import BaseRepository


class KeywordRepository(BaseRepository[Keyword]):
    """Repository handling specific data operations for the Keyword model."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Keyword)


async def get_keyword_repository(db: DbSessionDep) -> KeywordRepository:
    return KeywordRepository(db)


KeywordRepoDep = Annotated[KeywordRepository, Depends(get_keyword_repository)]
