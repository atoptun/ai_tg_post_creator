from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import settings
from app.utils.logger import logger


logger = logger.getChild("telegram_publisher")


def is_telegram_publish_enabled() -> bool:
    return all(
        [
            settings.TG_API_ID,
            settings.TG_API_HASH,
            settings.TG_BOT_SESSION_NAME,
            settings.TG_PUBLISH_CHANNEL,
        ]
    )


async def publish_post_to_telegram(message_text: str) -> bool:
    """Publish a generated post to the configured Telegram channel."""
    if not is_telegram_publish_enabled():
        logger.warning(
            "Telegram publishing is disabled; missing credentials or channel"
        )
        return False

    client = TelegramClient(
        settings.TG_BOT_SESSION_NAME,
        settings.TG_API_ID,
        settings.TG_API_HASH,
    )

    await client.start(bot_token=settings.TG_BOT_API_KEY) #type: ignore
    logger.info("Starting Client")
    try:
        message = await client.send_message(settings.TG_PUBLISH_CHANNEL, message_text)
        logger.info(f"Published message with id {message.id} to channel {settings.TG_PUBLISH_CHANNEL}")
    finally:
        await client.disconnect() #type: ignore

    return True
