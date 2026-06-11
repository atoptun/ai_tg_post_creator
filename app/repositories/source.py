from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DbSessionDep
from app.models import Source
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    """Repository handling specific data operations for the Source model."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Source)


async def get_source_repository(db: DbSessionDep) -> SourceRepository:
    return SourceRepository(db)


SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repository)]
