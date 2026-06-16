# Complete AI Telegram Post Creator Project

## Status Analysis
`task.md` transition Celery → FastStream success.

**Completed tasks:**
- [x] 1. Web news parsing (`task_parse_sites`, `pipeline.py`)
- [x] 3. News filtering (`_matches_keywords` in `pipeline.py`)
- [x] 4. AI-generation of posts (`generator.py`)
- [x] 5. Telegram publication (`telegram_publish.py`)
- [x] 6-8, 10. REST API endpoints (Sources, Keywords, Posts)
- [x] 11. Logging

**Pending tasks:**
- [ ] 2. Telegram news parsing. `app/news_parsers/telegram.py` disabled/dummy. `task_parse_telegram` in `app/tasks/parsers.py` commented out.
- [ ] 9. Manual generation (`/api/generate/`). Currently at `/news/{id}/generate`, needs exact route.
- [ ] README.md. Write setup instructions and API examples.

## Proposed Changes

### 1. Implement Telegram Parsing
Finalize `Telethon` client integration. Fetch recent messages from Telegram channels.

#### [MODIFY] [app/news_parsers/telegram.py](file:///home/topa/study/jr/projects/ai_tg_post_creator/app/news_parsers/telegram.py)
- Uncomment Telethon imports.
- Implement `parse_telegram_channel` to instantiate `TelegramClient`, fetch recent messages, format list of dictionaries for pipeline.

#### [MODIFY] [app/tasks/parsers.py](file:///home/topa/study/jr/projects/ai_tg_post_creator/app/tasks/parsers.py)
- Uncomment `task_parse_telegram`.
- Load `telegram` sources, schedule parsing, yield items to `pipeline.py` queue.

### 2. Manual Test Run Endpoint
Add endpoint `POST /sources/{source_id}/parse` to manually test a source parser immediately.

#### [MODIFY] [app/api/endpoints/sources.py](file:///home/topa/study/jr/projects/ai_tg_post_creator/app/api/endpoints/sources.py)
- Add endpoint `POST /{source_id}/parse`.
- Fetch source by ID.
- If `source.type == 'site'`, call `parse_site`. If `telegram`, call `parse_telegram_channel`.
- Push results to `filter-news-queue` via FastStream publisher.
- Return `{ "status": "queued", "fetched": <count> }`.
*(Note: News reprocessing `POST /news/{news_id}/generate` already exists)*

### 3. Manual Generation Endpoint
Add `POST /api/generate/` endpoint. Accept raw text or URL, call `generator.py` synchronously, return generated text.

### 4. Create README.md
Write comprehensive `README.md` with:
- Project description
- Docker run instructions
- API examples (curl)
