from datetime import timezone
from telethon import TelegramClient
from telethon.tl.types import Message
from app.config import settings
from app.utils.logger import logger


logger = logger.getChild("telegram_parser")


async def _fetch_channel(channel_username: str, source_name: str, limit: int = 20) -> list[dict]:
    items = []
    if not settings.TG_API_ID or not settings.TG_API_HASH:
        logger.warning("Telegram parsing is disabled (no credentials configured)")
        return []

    client = TelegramClient(
        settings.TG_SESSION_NAME or "telegram_session",
        settings.TG_API_ID,
        settings.TG_API_HASH,
    )
    try:
        await client.start(bot_token=settings.TG_BOT_API_KEY) #type: ignore
        async for message in client.iter_messages(channel_username, limit=limit):
            if not isinstance(message, Message) or not message.message:
                continue
            title = message.message[:100].replace("\n", " ")
            items.append(
                {
                    "title": title,
                    "url": None,
                    "summary": message.message[:500],
                    "source": source_name,
                    "published_at": message.date.replace(tzinfo=timezone.utc).replace( #type: ignore
                        tzinfo=None
                    ),
                    "raw_text": message.message,
                }
            )
    except Exception as e:
        logger.error(f"Error fetching Telegram channel {channel_username}: {e}")
    finally:
        await client.disconnect() #type: ignore
    return items


async def parse_telegram_channel(channel_username: str, source_name: str) -> list[dict]:
    """Parses recent messages from a Telegram channel and returns them in the same format as site parsing."""
    # logger.warning("Telegram parsing is disabled (no credentials configured)")
    # return []
    return await _fetch_channel(channel_username, source_name)
