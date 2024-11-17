from enum import Enum

from aiogram import F, Router, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command, or_f
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


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


async def start_help_info(message: types.Message, **kwargs):
    """
    Обработчик для команд /start, /help и кнопки Помощь

    Args:
        message (types.Message): Сообщение команд или кнопки
    """

    answer_text = """
    Привет! Данный бот создан в рамках пет-проекта по созданию и развёртывания ML модели

Нажмите на кнопки <b>"Одна поедка"</b> или <b>"Несколько поездок"</b> для получения предсказания стоимость поездки в Нью-Йорке.

Кнопки:
• <b>"Помощь"</b> - приведёт к информации по использованию бота
• <b>"Статистика бота"</b> - покажет статистику использования бота
• <b>"Информация о боте"</b> - расскажет о данных и модели, используемой в боте
    """
    builder = get_menu_buttons_builder()
    await message.answer(
        answer_text, parse_mode=ParseMode.HTML, reply_markup=builder.as_markup()
    )


@router.message(or_f(Command("start"), Command("help")))
async def start_help_command(message: types.Message, **kwargs):
    """Обработчик для команд /start и /help

    Args:
        message (types.Message): Сообщение команды /help
    """
    await start_help_info(message, **kwargs)


@router.callback_query(F.data == MenuButtonsData(action=MenuButtons.HELP).pack())
async def help_button(callback_query: types.CallbackQuery, **kwargs):
    """Обработчик для инлайн кнопки Помощь

    Args:
        callback_query (types.CallbackQuery): данные коллбэк кнопки Помощь
    """
    await start_help_info(callback_query.message, **kwargs)


@router.callback_query(F.data == MenuButtonsData(action=MenuButtons.INFO).pack())
async def info_button(callback_query: types.CallbackQuery, **kwargs):
    """Обработчик для инлайн кнопки 'Информация о боте'

    Args:
        callback_query (types.CallbackQuery): _description_
    """

    answer_text = """
Немного про бота:
• <a href="https://github.com/Arist0craft/taxi_fare_prediction">Ссылка на GitHub проекта</a>
• Автор бота - @DecadenceFull
• Язык проекта - Python3
• Модель под капотом - CatBoost
• Данные взяты с <a href="https://stepik.org/course/125501/syllabus">Курса Stepik</a>

Сам бот является лишь пэт-проектом, великого смысла не несёт
"""
    builder = get_menu_buttons_builder()
    await callback_query.message.answer(
        text=answer_text,
        parse_mode=ParseMode.HTML,
        link_preview_options=types.LinkPreviewOptions(is_disabled=True),
        reply_markup=builder.as_markup(),
    )
