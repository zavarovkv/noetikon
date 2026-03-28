import logging

from telegram.ext import Application

from noetikon.bot.router import register_handlers
from noetikon.config import get_settings
from noetikon.services.llm_service import LLMService

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()

    app = Application.builder().token(settings.telegram_bot_token).build()

    llm = LLMService(api_key=settings.anthropic_api_key, proxy_url=settings.anthropic_proxy)
    app.bot_data["llm"] = llm
    app.bot_data["settings"] = settings

    register_handlers(app)

    logger.info("Starting bot in webhook mode on port %s", settings.webhook_port)
    app.run_webhook(
        listen="0.0.0.0",
        port=settings.webhook_port,
        url_path="/webhook",
        webhook_url=f"{settings.webhook_url}/webhook",
    )


if __name__ == "__main__":
    main()
