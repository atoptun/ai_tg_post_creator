from sqlalchemy import func, select
from fastapi import APIRouter

from app.api.schemas import MonitoringSummary, PostOut
from app.db import DbSessionDep
from app.models import Keyword, NewsItem, Post, Source


router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/summary", response_model=MonitoringSummary)
async def monitoring_summary(db: DbSessionDep):
    """Return a compact operational snapshot for the ingestion and publishing pipeline."""

    sources_total = await db.scalar(select(func.count()).select_from(Source)) or 0
    sources_enabled = (
        await db.scalar(select(func.count()).select_from(Source).where(Source.enabled))
        or 0
    )
    keywords_total = await db.scalar(select(func.count()).select_from(Keyword)) or 0
    news_items_total = await db.scalar(select(func.count()).select_from(NewsItem)) or 0
    posts_total = await db.scalar(select(func.count()).select_from(Post)) or 0

    status_rows = await db.execute(
        select(Post.status, func.count()).group_by(Post.status)
    )
    posts_by_status = {status: count for status, count in status_rows.all()}

    failed_posts_result = await db.execute(
        select(Post).where(Post.status == "failed").order_by(Post.id.desc()).limit(5)
    )
    recent_failed_posts = list(failed_posts_result.scalars().all())

    return MonitoringSummary(
        sources_total=sources_total,
        sources_enabled=sources_enabled,
        keywords_total=keywords_total,
        news_items_total=news_items_total,
        posts_total=posts_total,
        posts_by_status=posts_by_status,
        recent_failed_posts=recent_failed_posts,
    )
