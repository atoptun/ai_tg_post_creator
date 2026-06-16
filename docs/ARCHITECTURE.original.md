# AI Telegram Post Creator - Architecture

## Overview
This project is an automated system that parses news from various sources (web, Telegram), processes the content using AI (OpenAI), and automatically publishes formatted posts to Telegram. It uses a microservices-like architecture running in Docker, orchestrated via Docker Compose.

## Core Technologies
- **API Framework**: FastAPI
- **Message Broker & Task Queue**: FastStream with RabbitMQ
- **Database**: PostgreSQL (with SQLAlchemy, Asyncpg, Alembic)
- **Caching**: Redis
- **Web Parsing**: BeautifulSoup4, lxml
- **Telegram Client**: Telethon
- **AI Processing**: OpenAI API

## System Components (Docker Services)
1. **Nginx**: Reverse proxy for incoming requests.
2. **API (FastAPI)**: Exposes REST endpoints to manage sources, keywords, and monitor the system.
3. **Worker (FastStream)**: Consumes messages from RabbitMQ to perform heavy background tasks (parsing sites, AI generation, publishing).
4. **Scheduler (FastStream)**: Triggers periodic tasks (e.g., triggering parsers at specific intervals).
5. **Infrastructure**: PostgreSQL (data storage), RabbitMQ (message broker), Redis (caching), pgAdmin (DB management).

## Project Structure
- `app/` - Main application code.
  - `api_app.py` - Entrypoint for the FastAPI application.
  - `worker_app.py` - Entrypoint for the FastStream worker.
  - `scheduler_app.py` - Entrypoint for the FastStream scheduler.
  - `api/` - REST API routes, Pydantic schemas, and endpoints.
  - `ai/` - OpenAI integration logic and prompts.
  - `news_parsers/` - Logic for scraping and parsing external news sites and Telegram channels.
  - `repositories/` - Database access layer (Data Access Objects for `news_item`, `post`, `source`, etc.).
  - `tasks/` - FastStream task definitions (`parsers.py`, `pipeline.py`, `telegram_publish.py`).
  - `telegram/` - Telethon-based client for publishing messages to Telegram.
  - `models.py` - SQLAlchemy ORM models.
  - `db.py` - Database connection and session management.
  - `config.py` - Environment variables configuration.
- `alembic/` - Database migrations.
- `tests/` - Pytest automated tests.
- `compose*.yml` - Docker Compose definitions for dev/prod environments.
- `task.md` - Task description.
