# from telethon import TelegramClient
# from telethon.tl.types import Message
# from app.config import settings
from app.utils.logger import logger


logger = logger.getChild("telegram_parser")


# async def _fetch_channel(channel_username: str, source_name: str, limit: int = 20) -> list[dict]:
#     items = []
#     client = TelegramClient(
#         settings.TELEGRAM_SESSION,
#         settings.TELEGRAM_API_ID,
#         settings.TELEGRAM_API_HASH,
#     )
#     try:
#         await client.start()
#         async for message in client.iter_messages(channel_username, limit=limit):
#             if not isinstance(message, Message) or not message.text:
#                 continue
#             title = message.text[:100].replace("\n", " ")
#             items.append({
#                 "title": title,
#                 "url": None,
#                 "summary": message.text[:500],
#                 "source": source_name,
#                 "published_at": message.date.replace(tzinfo=timezone.utc),
#                 "raw_text": message.text,
#             })
#     except Exception as e:
#         logger.error(f"Error fetching Telegram channel {channel_username}: {e}")
#     finally:
#         await client.disconnect()
#     return items


async def parse_telegram_channel(channel_username: str, source_name: str) -> list[dict]:
    """Parses recent messages from a Telegram channel and returns them in the same format as site parsing."""
    logger.warning("Telegram parsing is disabled (no credentials configured)")
    return []
    # return asyncio.run(_fetch_channel(channel_username, source_name))
