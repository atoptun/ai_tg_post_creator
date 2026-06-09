from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


postgres_engine = create_async_engine(settings.postgres_url, echo=True)

AsyncSessionLocal = async_sessionmaker(
    postgres_engine, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
