# AI Telegram Post Creator

Automated system for parsing news from web sources and Telegram channels, generating engaging posts via OpenAI, and publishing them to a Telegram channel.

## Architecture

- **API Framework**: FastAPI
- **Background Tasks**: FastStream + RabbitMQ
- **Database**: PostgreSQL
- **Parsers**: BeautifulSoup4, lxml, Telethon
- **AI**: OpenAI API

## Setup and Running (Docker)

1. Copy `.env.example` to `.env` and fill in the values (Postgres, RabbitMQ, OpenAI API key, Telegram credentials).
2. Start the services:
   ```bash
   make doc-start-dev
   # or natively with docker compose
   docker compose -f compose.yml -f compose.dev.yml up -d --build
   ```
3. The API will be available at `http://localhost:8000/docs`.

## API Examples

**Add a new site source:**
```bash
curl -X POST "http://localhost:8000/api/sources/" \
     -H "Content-Type: application/json" \
     -d '{"name": "TechCrunch", "url": "https://techcrunch.com", "type": "site", "enabled": true}'
```

**Add a Telegram source:**
```bash
curl -X POST "http://localhost:8000/api/sources/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Breaking News", "url": "breaking_news", "type": "telegram", "enabled": true}'
```

**Manually trigger parsing for a source:**
```bash
curl -X POST "http://localhost:8000/api/sources/1/parse"
```

**Test AI generation manually:**
```bash
curl -X POST "http://localhost:8000/api/generate/" \
     -H "Content-Type: application/json" \
     -d '{"raw_text": "Apple just announced the new iPhone 16..."}'
```
