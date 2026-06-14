from typing import Any, Generic, TypeVar
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    A Generic Repository pattern implementation providing base CRUD and pagination operations.
    """

    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model

        mapper = inspect(self.model)
        self._non_nullable_fields = {
            col.key for col in mapper.columns if not col.nullable
        }

    async def create(self, **kwargs: Any) -> ModelType:
        """Insert a new record into the database."""
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, id_val: int) -> ModelType | None:
        """Retrieve a specific record by its primary key ID."""
        return await self.db.get(self.model, id_val)

    async def update(self, db_obj: ModelType, **kwargs: Any) -> ModelType:
        """Partially update an existing database object using strict Pydantic schemas."""
        for field, value in kwargs.items():
            if hasattr(db_obj, field):
                if not (value is None and field in self._non_nullable_fields):
                    setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Completely remove an entity from the tracking registry."""
        await self.db.delete(db_obj)
        await self.db.commit()

    async def get_paginated_list(self, params: Params | None = None) -> Page[ModelType]:
        """Returns a paginated list for the target model using async pagination context."""
        query = select(self.model)
        return await apaginate(self.db, query, params=params)

    async def get_list(self) -> list[ModelType]:
        """Returns all records for the target model without pagination."""
        result = await self.db.scalars(select(self.model))
        return list(result.all())
