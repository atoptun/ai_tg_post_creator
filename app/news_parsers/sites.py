# import requests
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

from app.utils.logger import logger


logger = logger.getChild(__name__)


async def parse_site(url: str, source_name: str) -> list[dict]:
    """
    Generic HTML scraper. Finds <article> tags or falls back to divs with
    'news' in their class name. Returns dicts matching NewsItem fields.
    """
    items = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        articles = soup.find_all("article")
        if not articles:
            articles = soup.find_all("div", class_=lambda c: c and "news" in c.lower()) # type: ignore

        for article in articles[:5]:
            title_tag = article.find(["h1", "h2", "h3", "a"])
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title:
                continue

            link_tag = article.find("a", href=True)
            article_url = link_tag["href"] if link_tag else None
            if article_url and article_url.startswith("/"):  # type: ignore
                article_url = urljoin(url, article_url)  # type: ignore

            paragraphs = article.find_all("p")
            raw_text = " ".join(p.get_text(strip=True) for p in paragraphs)
            summary = raw_text[:500] if raw_text else title

            items.append(
                {
                    "title": title,
                    "url": article_url,
                    "summary": summary,
                    "source": source_name,
                    "published_at": datetime.now(timezone.utc),
                    "raw_text": raw_text,
                }
            )

    except Exception as e:
        logger.error(f"Error parsing site {url}: {e}")

    return items
