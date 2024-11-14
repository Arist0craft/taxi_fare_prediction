from aiogram.types import Update
from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from src.bot import Bot, Dispatcher, get_bot, get_dispatcher
from src.settings import Settings, get_settings

settings: Settings = get_settings()

router = APIRouter()


@router.post("/bot")
async def webhook(
    update: Update,
    dispatcher: Annotated[Dispatcher, Depends(get_dispatcher)],
    bot: Annotated[Bot, Depends(get_bot)],
):
    await dispatcher.feed_update(bot=bot, update=update)
