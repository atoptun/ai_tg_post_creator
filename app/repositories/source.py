from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import DbSessionDep
from app.models import Source
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    """Repository handling specific data operations for the Source model."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Source)

    async def get_enabled_sources_by_type(self, source_type: str) -> list[Source]:
        """Returns a list of active sources filtered by their type (e.g., "site" or "tg")."""

        query = select(self.model).where(
            self.model.type == source_type,
            self.model.enabled,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


async def get_source_repository(db: DbSessionDep) -> SourceRepository:
    return SourceRepository(db)


SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repository)]
