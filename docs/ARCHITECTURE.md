# AI Telegram Post Creator - Architecture

## Overview
Automated system. Parse news (web, Telegram) → AI (OpenAI) process → publish formatted posts to Telegram. Microservices architecture in Docker via Docker Compose.

## Core Technologies
- **API Framework**: FastAPI
- **Message Broker & Task Queue**: FastStream + RabbitMQ
- **Database**: PostgreSQL (SQLAlchemy, Asyncpg, Alembic)
- **Caching**: Redis
- **Web Parsing**: BeautifulSoup4, lxml
- **Telegram Client**: Telethon
- **AI Processing**: OpenAI API

## System Components (Docker Services)
1. **Nginx**: Reverse proxy for incoming requests.
2. **API (FastAPI)**: REST endpoints manage sources, keywords, monitor system.
3. **Worker (FastStream)**: Consume RabbitMQ messages. Heavy tasks (parse sites, AI generation, publish).
4. **Scheduler (FastStream)**: Trigger periodic tasks (e.g., parsers).
5. **Infrastructure**: PostgreSQL (data), RabbitMQ (broker), Redis (cache), pgAdmin (DB admin).

## Project Structure
- `app/` - Main app code.
  - `api_app.py` - Entrypoint FastAPI.
  - `worker_app.py` - Entrypoint FastStream worker.
  - `scheduler_app.py` - Entrypoint FastStream scheduler.
  - `api/` - REST API routes, Pydantic schemas, endpoints.
  - `ai/` - OpenAI logic + prompts.
  - `news_parsers/` - Scrape/parse news sites + Telegram channels.
  - `repositories/` - DB access (DAOs for `news_item`, `post`, `source`).
  - `tasks/` - FastStream tasks (`parsers.py`, `pipeline.py`, `telegram_publish.py`).
  - `telegram/` - Telethon client publish messages to Telegram.
  - `models.py` - SQLAlchemy ORM models.
  - `db.py` - DB connection + session management.
  - `config.py` - Env vars config.
- `alembic/` - DB migrations.
- `tests/` - Pytest tests.
- `compose*.yml` - Docker Compose dev/prod.
- `task.md` - Task description.
