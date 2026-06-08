from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
    app_name: str = "Telegram bot. FastAPI API"
    
    debug: bool = False

    log_level: str = "info"
    log_file: str = "/app/logs/web.log"

    # mongodb_uri: str = "mongodb://root:root@mongo:27017"
    # mongodb_database_name: str = "shop_db"

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"


settings = Settings()
