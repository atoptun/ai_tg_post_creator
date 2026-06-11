from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page

from app.db import DbSessionDep
from app.models import Source
from app.api.schemas import SourceCreate, SourceUpdate


class SourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_paginated_list(self) -> Page:
        """Returns a paginated list of sources."""
        return await paginate(self.db, select(Source))

    async def get_by_id(self, source_id: int) -> Source | None:
        """Finds a single source by its ID."""
        return await self.db.get(Source, source_id)

    async def create(self, data: SourceCreate) -> Source:
        """Creates and saves a new source."""
        source = Source(**data.model_dump())
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def update(self, source: Source, data: SourceUpdate) -> Source:
        """Updates fields of an existing source."""
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(source, field, value)
        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def delete(self, source: Source) -> None:
        """Deletes a source from the database."""
        await self.db.delete(source)
        await self.db.commit()


def get_source_repository(db: DbSessionDep) -> SourceRepository:
    return SourceRepository(db)


SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repository)]
