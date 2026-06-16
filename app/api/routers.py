from fastapi import APIRouter

from app.api.endpoints.sources import router as sources_router
from app.api.endpoints.keywords import router as keywords_router
from app.api.endpoints.news import router as news_router
from app.api.endpoints.posts import router as posts_router
from app.api.endpoints.monitoring import router as monitoring_router
from app.api.endpoints.trigers import router as trigers_router

api_router = APIRouter(prefix="/api")

api_router.include_router(sources_router)
api_router.include_router(keywords_router)
api_router.include_router(news_router)
api_router.include_router(posts_router)
api_router.include_router(monitoring_router)
api_router.include_router(trigers_router)
