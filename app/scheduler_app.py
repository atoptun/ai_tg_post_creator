from typing import AsyncGenerator

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from taskiq_faststream import BrokerWrapper, StreamScheduler
from taskiq.schedule_sources import LabelScheduleSource


from app.config import settings

# from app.stream_app import broker
from app.utils.logger import logger
from app.repositories.source import SourceRepository
from app.tasks.parsers import parse_sites_task  # , parse_telegram_task
from app.utils.scheduler import repo_context


logger = logger.getChild("scheduler")

broker = RabbitBroker(settings.rabbitmq_url)

app = FastStream(broker)

taskiq_broker = BrokerWrapper(broker)


async def scheduled_parse_sites() -> AsyncGenerator[list[dict], None]:
    """
    Wrapper that acts as an event generator for Taskiq.
    Every yielded list[dict] will be automatically sent to RabbitMQ.
    """
    async with repo_context(SourceRepository) as source_repo:
        # Просто проксіюємо yield з нашої основної таски
        async for items in parse_sites_task(source_repo):
            yield items


scheduled_parse_sites_producer = taskiq_broker.task(
    message=scheduled_parse_sites,
    queue="filter-news-queue",
    schedule=[
        {
            "cron": "*/1 * * * *",
        }
    ],
)

scheduler = StreamScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)


REGISTERED_PRODUCERS = (scheduled_parse_sites_producer,)
