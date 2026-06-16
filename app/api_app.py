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
    from app.worker_app import broker

    try:
        await broker.connect()
        logger.info("FastStream broker connected")
    except Exception as e:
        logger.error(f"Failed to connect FastStream broker: {e}")

    yield

    # Shutdown code
    logger.info("Shutting down...")
    try:
        await broker.stop()
        logger.info("FastStream broker connection closed")
    except Exception as e:
        logger.error(f"Failed to stop FastStream broker: {e}")


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)

add_pagination(app)


@app.get("/")
async def get_root():
    return {"app": settings.app_name}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
