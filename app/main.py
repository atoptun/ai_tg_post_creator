from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.config import settings
from app.utils.logger import logger
from app.api.routers import api_router

logger = logger.getChild("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up...")

    # async with postgres_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield
    # Shutdown code
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)

add_pagination(app)


@app.get("/")
async def get_root():
    return { "app": settings.app_name }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/test")
async def test_endpoint():
    pass
