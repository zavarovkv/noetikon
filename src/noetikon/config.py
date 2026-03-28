from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    telegram_bot_token: str
    webhook_url: str
    webhook_port: int = 8443

    # Anthropic
    anthropic_api_key: str
    anthropic_proxy: str

    # CalDAV
    caldav_url: str
    caldav_username: str
    caldav_password: str

    # Database
    database_url: str

    # Behavior
    humor_frequency: int = 30
    llm_rate_limit: int = 50

    # Admin panel
    admin_username: str = "admin"
    admin_password: str
    admin_port: int = 8080

    # Alerts
    alert_chat_id: int | None = None


def get_settings() -> Settings:
    return Settings()
