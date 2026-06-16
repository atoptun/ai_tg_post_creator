import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # env_file=".env",
        extra="ignore",
    )
    app_name: str = "Telegram bot. FastAPI API"

    debug: bool = False

    log_level: str = "info"
    log_file: str = ""

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASS: str

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MODEL_TEMPERATURE: float = 0.7

    TG_API_ID: int = 0
    TG_API_HASH: str = ""
    TG_USER_SESSION_NAME: str = "tg_user"
    TG_BOT_SESSION_NAME: str = "tg_bot"
    TG_PUBLISH_CHANNEL: int = 0
    TG_BOT_API_KEY: str = ""

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"
        )


settings = Settings(_env_file=os.getenv("ENV", ".env"))  # type: ignore
