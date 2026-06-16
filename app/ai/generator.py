import asyncio
from openai import RateLimitError, APIStatusError
from app.ai.openai_client import get_openai_client

from app.config import settings
from app.utils.logger import logger

logger = logger.getChild(__name__)


PROMPT_TEMPLATE = (
    "Зроби короткий, цікавий опис новини для Telegram-каналу, "
    "додай емодзі (emoji), call to action. "
    "Новина:\n\nЗаголовок: {title}\n\nТекст: {text}"
)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class EmptyTextException(Exception):
    pass

async def generate_post_text(news) -> str | None:
    client = get_openai_client()
    prompt = PROMPT_TEMPLATE.format(
        title=news.title,
        text=(news.summary or news.raw_text or "")[:1500],
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=settings.OPENAI_MODEL_TEMPERATURE,
            )
            ai_text = str(response.choices[0].message.content).strip()
            if len(ai_text) == 0:
                raise EmptyTextException("Empty text from AI")
            
            generated_text = f"{ai_text}\nДжерело:{news.url}"
            logger.info(generated_text)
            return generated_text

        except RateLimitError as e:
            wait = RETRY_DELAY * attempt
            logger.warning(
                f"OpenAI rate limit hit (attempt {attempt}/{MAX_RETRIES}), retrying in {wait}s: {e}"
            )
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(wait)
            continue

        except APIStatusError as e:
            logger.error(f"OpenAI API error {e.status_code}: {e.message}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise
    return None
