# import logging
from faststream import FastStream, Context, Logger
from faststream.rabbit import RabbitBroker, RabbitRouter

from app.config import settings
from app.utils.logger import logger
from app.tasks.filter import router as filter_router
from app.tasks.generator import router as generator_router
from app.tasks.telegram_publish import router as telegram_publish_router
from app.tasks.parsers import router as parsers_router


logger = logger.getChild("app")


broker = RabbitBroker(settings.rabbitmq_url)

broker.include_router(filter_router)
broker.include_router(generator_router)
broker.include_router(telegram_publish_router)
broker.include_router(parsers_router)

app = FastStream(broker)


@app.on_startup
async def startup(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} started")
    pass


@app.on_shutdown
async def shutdown(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} stopped")
    pass
