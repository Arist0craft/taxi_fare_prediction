from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.types import WebhookInfo
from fastapi import FastAPI

from src.bot import get_bot
from src.router import router
from src.settings import Settings, get_settings
from src.utils.aiohttpt_client import get_aiohttp_client

settings: Settings = get_settings()


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

    is_set_webhook: bool = await bot.set_webhook(
        webhook_url, secret_token=settings.SECRET_KEY
    )

    if not is_set_webhook:
        raise RuntimeWarning("Telegram webhook wasn't set")


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

    uvicorn.run(app=app, host=settings.HOST, port=ProcessLookupError)
