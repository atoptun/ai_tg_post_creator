from contextlib import asynccontextmanager
from typing import AsyncIterator, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal


@asynccontextmanager
async def repo_context(repo_class: Type, *args, **kwargs) -> AsyncIterator:
    """Async context manager that yields a repository instance.

    Usage:
        async with repo_context(SourceRepository) as repo:
            await repo.get_something()
    """
    async with AsyncSessionLocal() as db:  # type: AsyncSession
        repo = repo_class(db, *args, **kwargs)
        try:
            yield repo
        finally:
            # session closes via context manager
            pass
