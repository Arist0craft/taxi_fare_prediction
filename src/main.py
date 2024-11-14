from contextlib import asynccontextmanager

from aiogram.types import WebhookInfo
from fastapi import APIRouter, FastAPI

from src.bot import get_bot
from src.router import router as bot_router
from src.settings import Settings, get_settings

settings: Settings = get_settings()


async def set_webhook():
    """Установка вебхука телеграм бота на старте приложения

    Raises:
        RuntimeWarning: если вебхук установлен неудачно
    """

    bot = get_bot()

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
    await set_webhook()
    yield


router = APIRouter()


@router.get("/")
async def check() -> dict[str, str]:
    return {"status": "ok, api is wooooooooooooOOsh?..."}


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(lifespan=lifespan)
    app.include_router(router=router)
    app.include_router(router=bot_router)
    return app


app = create_app()
