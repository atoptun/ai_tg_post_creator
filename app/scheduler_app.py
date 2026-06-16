from typing import AsyncGenerator

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from taskiq_faststream import BrokerWrapper, StreamScheduler
from taskiq.schedule_sources import LabelScheduleSource


from app.config import settings

# from app.stream_app import broker
from app.utils.logger import logger
from app.repositories.source import SourceRepository
from app.tasks.parsers import task_parse_sites, task_parse_telegram
from app.utils.scheduler import repo_context


logger = logger.getChild("scheduler")

broker = RabbitBroker(settings.rabbitmq_url)

app = FastStream(broker)

taskiq_broker = BrokerWrapper(broker)


async def scheduled_parse_sites() -> AsyncGenerator[list[dict], None]:
    async with repo_context(SourceRepository) as source_repo:
        async for items in task_parse_sites(source_repo):
            yield items


scheduled_parse_sites_producer = taskiq_broker.task(
    message=scheduled_parse_sites,
    queue="filter-news-queue",
    schedule=[
        {
            "cron": "0,30 * * * *",
        }
    ],
)

async def scheduled_parse_telegram() -> AsyncGenerator[list[dict], None]:
    async with repo_context(SourceRepository) as source_repo:
        async for items in task_parse_telegram(source_repo):
            yield items


scheduled_parse_telegram_producer = taskiq_broker.task(
    message=scheduled_parse_telegram,
    queue="filter-news-queue",
    schedule=[{"cron": "0,30 * * * *"}],
)


scheduler = StreamScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)


REGISTERED_PRODUCERS = (scheduled_parse_sites_producer, scheduled_parse_telegram_producer)
