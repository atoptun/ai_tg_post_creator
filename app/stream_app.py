# import logging
from faststream import FastStream, Context, Logger
from faststream.rabbit import RabbitBroker, RabbitRouter

from app.config import settings
from app.utils.logger import logger
from app.tasks.pipeline import router as pipeline_router
from app.tasks.telegram_publish import router as telegram_publish_router


logger = logger.getChild("stream_app")


broker = RabbitBroker(settings.rabbitmq_url)
router = RabbitRouter()

broker.include_router(router)
broker.include_router(pipeline_router)
broker.include_router(telegram_publish_router)
app = FastStream(broker)

inQueuePublisher = broker.publisher("in-queue")


@app.on_startup
async def startup(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} started")
    pass


@app.on_shutdown
async def shutdown(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} stopped")
    pass


@app.after_startup
async def test():
    await inQueuePublisher.publish(
        message={"user": "John", "user_id": 1},
    )


@broker.subscriber("in-queue")
# @broker.publisher("out-queue")
async def handle_msg(user: str, user_id: int, logger: Logger) -> None:
    logger.info(f"Processing message for user: {user_id} - {user}")
    # return f"User: {user_id} - {user} registered"
