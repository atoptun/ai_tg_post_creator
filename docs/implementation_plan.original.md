# Complete AI Telegram Post Creator Project

## Status Analysis
Based on `task.md`, the project has transitioned from Celery to FastStream successfully.

**Completed tasks:**
- [x] 1. Web news parsing (`parse_sites_task`, `pipeline.py`)
- [x] 3. News filtering (`_matches_keywords` in `pipeline.py`)
- [x] 4. AI-generation of posts (`generator.py`)
- [x] 5. Telegram publication (`telegram_publish.py`)
- [x] 6-10. REST API endpoints (Sources, Keywords, Posts, News manual generation)
- [x] 11. Logging

**Pending tasks:**
- [ ] 2. Telegram news parsing. The code in `app/news_parsers/telegram.py` is currently disabled/dummy, and `parse_telegram_task` in `app/tasks/parsers.py` is commented out.

## Proposed Changes

### 1. Implement Telegram Parsing
We need to finalize the `Telethon` client integration for fetching recent messages from Telegram channels.

#### [MODIFY] [app/news_parsers/telegram.py](file:///home/topa/study/jr/projects/ai_tg_post_creator/app/news_parsers/telegram.py)
- Uncomment the Telethon imports.
- Implement the `parse_telegram_channel` function to instantiate the `TelegramClient`, fetch recent messages, and format them into a list of dictionaries matching the pipeline expected input.

#### [MODIFY] [app/tasks/parsers.py](file:///home/topa/study/jr/projects/ai_tg_post_creator/app/tasks/parsers.py)
- Uncomment the `parse_telegram_task`.
- Ensure it properly loads `telegram` sources and schedules parsing, yielding items to the same `pipeline.py` queue.
