from contextlib import asynccontextmanager
from faststream import FastStream, Context, ContextRepo
from faststream.rabbit import RabbitBroker, RabbitRouter

from app.config import settings
from app.utils.logger import logger


logger = logger.getChild("stream_app")


@asynccontextmanager
async def lifespan(context: ContextRepo):
    logger.info("Starting FastStream application...")
    yield
    logger.info("Shutting down FastStream application...")


broker = RabbitBroker(settings.rabbitmq_url)
router = RabbitRouter()

broker.include_router(router)
app = FastStream(broker, lifespan=lifespan)


@app.on_startup
async def startup(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} started")


@app.on_shutdown
async def shutdown(worker_id: int | None = Context(default=None)) -> None:
    logger.info(f"Worker {worker_id} stopped")


@broker.subscriber("test-queue")
async def base_handler(msg_body: int):
    logger.info(f"Received message: {msg_body}")

@broker.subscriber("test-user-queue")
async def user_handler(user_id: int, name: str):
    logger.info(f"Received user message: {user_id} - {name}")


