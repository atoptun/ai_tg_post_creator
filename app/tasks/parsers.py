from typing import AsyncIterator, Annotated

from app.db import AsyncSessionLocal
from app.repositories.source import SourceRepository, get_source_repository
from app.news_parsers.sites import parse_site
from app.news_parsers.telegram import parse_telegram_channel
from app.utils.logger import logger

from faststream import Depends
from faststream.rabbit import RabbitRouter

logger = logger.getChild("parsers")

router = RabbitRouter()
filter_publisher = router.publisher("filter-news-queue")
run_parser_publisher = router.publisher("run-parser-queue")

SourceRepoDep = Annotated[SourceRepository, Depends(get_source_repository)]
# SourceRepository = StreamDepends(get_source_repository)


async def task_parse_sites(
    source_repo: SourceRepoDep,
) -> AsyncIterator[list[dict]]:
    """
    Periodic task that fetches active site sources.
    """
    logger.info("Starting scheduled site parsing task...")
    sources = await source_repo.get_enabled_sources_by_type(source_type="site")

    if not sources:
        logger.info("No enabled site sources found. Skipping.")
        return

    total_fetched = 0
    for source in sources:
        try:
            logger.info(f"Parsing site source: {source.name} ({source.url})")
            items = await parse_site(source.url, source.name)
            if not items:
                continue

            total_fetched += len(items)
            # await broker.publish(message=items, queue="raw-items-queue")
            logger.info(f"Successfully pushed {len(items)} items from {source.name}")
            yield items

        except Exception as e:
            logger.error(f"Failed to parse site source {source.name}: {str(e)}")

    logger.info(f"Finished parsing sites. Total items queued: {total_fetched}")


async def task_parse_telegram(
    source_repo: SourceRepoDep,
) -> AsyncIterator[list[dict]]:
    """
    Periodic task that fetches active Telegram channels, parses fresh messages,
    and pushes them to the same pipeline for checking and filtering.
    """
    logger.info("Starting scheduled Telegram parsing task...")
    sources = await source_repo.get_enabled_sources_by_type(source_type="tg")

    if not sources:
        logger.info("No enabled Telegram sources found. Skipping.")
        return

    total_fetched = 0
    for source in sources:
        try:
            logger.info(f"Parsing Telegram channel: {source.name} ({source.url})")
            items = await parse_telegram_channel(source.url, source.name)
            if not items:
                continue

            total_fetched += len(items)
            logger.info(
                f"Successfully fetched {len(items)} items from telegram: {source.name}"
            )
            yield items

        except Exception as e:
            logger.error(f"Failed to parse Telegram source {source.name}: {str(e)}")

    logger.info(f"Finished parsing Telegram. Total items queued: {total_fetched}")


@router.subscriber("run-parser-queue")
async def task_run_parser(source: str) -> None:
    """
    Consumer that manually runs either site or telegram parsing depending on `source` parameter,
    and forwards fetched items to filter-news-queue.
    """
    logger.info(f"Manual parser execution requested for source: {source}")

    total_items = 0
    async with AsyncSessionLocal() as db:
        source_repo = SourceRepository(db)
        if source == "site":
            async for items in task_parse_sites(source_repo):
                if items:
                    total_items += len(items)
                    await filter_publisher.publish(items)
        elif source == "tg":
            async for items in task_parse_telegram(source_repo):
                if items:
                    total_items += len(items)
                    await filter_publisher.publish(items)
        else:
            logger.error(f"Unknown parser source: {source}")
            return

    logger.info(
        f"Manual parsing finished for source: {source}. Total items forwarded: {total_items}"
    )
