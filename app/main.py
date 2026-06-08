from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up...")

    yield
    # Shutdown code
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def get_root():
    return { "app": settings.app_name }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
