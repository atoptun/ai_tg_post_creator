from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Source


DEFAULT_TEST_SOURCE = {
    "name": "Liga News Site",
    "type": "site",
    "url": "https://www.liga.net/ua",
    "enabled": True,
}


async def seed_test_source(session: AsyncSession) -> Source:
    """Create or reuse a stable site source for scheduler and repository tests."""
    result = await session.execute(
        select(Source).where(Source.url == DEFAULT_TEST_SOURCE["url"])
    )
    source = result.scalar_one_or_none()

    if source is not None:
        return source

    source = Source(**DEFAULT_TEST_SOURCE)
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def seed_default_sources() -> list[Source]:
    """Seed the default set of sources into the configured database."""
    async with AsyncSessionLocal() as session:
        source = await seed_test_source(session)
        return [source]


async def main() -> None:
    sources = await seed_default_sources()
    for source in sources:
        print(f"seeded source: {source.id} {source.name} {source.url}")


if __name__ == "__main__":
    asyncio.run(main())
