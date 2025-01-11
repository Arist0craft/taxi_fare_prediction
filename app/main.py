import logging
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, WebhookInfo
from fastapi import FastAPI

from app.bot import get_bot
from app.router import router
from app.settings import Settings, get_settings
from app.utils.aiohttpt_client import get_aiohttp_client
from app.utils.logging_settings import setup_logging

settings: Settings = get_settings()
setup_logging()

logger = logging.getLogger(__name__)


async def set_webhook(bot: Bot):
    """Установка вебхука телеграм бота на старте приложения

    Raises:
        RuntimeWarning: если вебхук установлен неудачно
    """

    if (webhook_url := str(settings.TG_WEBHOOK_URL))[-1] == "/":
        webhook_url = str(settings.TG_WEBHOOK_URL)[:-1]

    webhook_url += "/" + "bot"

    webhook_info: WebhookInfo = await bot.get_webhook_info()

    if webhook_info.url == webhook_url:
        return

    certificate = None
    if (
        settings.TG_WEBHOOK_CERTIFICATE is not None
        and settings.TG_WEBHOOK_CERTIFICATE.strip() != ""
    ):
        certificate = BufferedInputFile(
            bytes(settings.TG_WEBHOOK_CERTIFICATE, "utf-8"), "cert.pem"
        )
    try:
        is_set_webhook: bool = await bot.set_webhook(
            webhook_url, secret_token=settings.SECRET_KEY, certificate=certificate
        )
        if is_set_webhook:
            logger.info("Webhook was set!")
        else:
            logger.info("Webhook wasn't set, debug error")

    except TelegramBadRequest as err:
        logger.error(err)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менедежер для задач перед запуском и после запуска приложения

    Args:
        app (FastAPI): Приложение FastAPI
    """
    bot = get_bot()
    await set_webhook(bot)

    yield
    aiohttp_client = get_aiohttp_client()
    await aiohttp_client.close()
    await bot.session.close()


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(lifespan=lifespan)
    app.include_router(router=router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        log_config=str(settings.LOGGING_CONFIG_PATH),
    )
