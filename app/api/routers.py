from fastapi import APIRouter

from app.api.endpoints.sources import router as sources_router
# from app.api.endpoints.keywords import router as keywords_router # твої майбутні модулі

api_router = APIRouter(prefix="/api")

api_router.include_router(sources_router)
# api_router.include_router(keywords_router)
