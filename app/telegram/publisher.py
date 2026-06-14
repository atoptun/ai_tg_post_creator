from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import settings
from app.utils.logger import logger


logger = logger.getChild("telegram_publisher")


def is_telegram_publish_enabled() -> bool:
    return all(
        [
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
            settings.TELEGRAM_SESSION,
            settings.TELEGRAM_CHANNEL,
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
        StringSession(settings.TELEGRAM_SESSION),
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )

    async with client:
        await client.send_message(settings.TELEGRAM_CHANNEL, message_text)

    return True
