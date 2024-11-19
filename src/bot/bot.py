from functools import lru_cache

from aiogram import Bot, Dispatcher

from src.bot.main_router import router
from src.bot.single_predicion_router import router as single_prediction_router
from src.settings import Settings, get_settings

settings: Settings = get_settings()


@lru_cache
def get_bot() -> Bot:
    return Bot(token=settings.TG_BOT_TOKEN)


@lru_cache
def get_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher.include_router(single_prediction_router)

    return dispatcher
