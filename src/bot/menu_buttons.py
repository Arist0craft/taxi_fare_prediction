from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuButtons(Enum):
    SINGLE_PREDICTION = 1
    BATCH_PREDICTION = 2
    HELP = 3
    RATING = 4
    INFO = 5


class MenuButtonsData(CallbackData, prefix="menu"):
    action: MenuButtons


def get_menu_buttons_builder() -> InlineKeyboardBuilder:
    """Создание кнопок - меню для всех сообщений

    Returns:
        InlineKeyboardBuilder: Строитель кнопок для меню
    """
    button_texts = [
        "Одна поездка",
        "Несколько поездок",
        "Помощь",
        "Статистика бота",
        "Информация о боте",
    ]

    builder = InlineKeyboardBuilder()
    for text, data in zip(button_texts, MenuButtons):
        builder.button(text=text, callback_data=MenuButtonsData(action=data))

    builder.adjust(2)
    return builder
