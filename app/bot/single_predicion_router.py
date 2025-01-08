import re

import aiohttp
from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import ValidationError

from app.bot.menu_buttons import MenuButtons, MenuButtonsData
from app.bot.validators import validate_coordinates, validate_datetime
from app.model import TaxiTravel, predict
from app.utils.geocode_client import geocode_client


class SinglePredictionStates(StatesGroup):
    pickup_point_enter = State()
    dropoff_point_enter = State()
    passengers_count_enter = State()
    pickup_date_enter = State()


router = Router()


async def flow_enter(message: types.Message, state: FSMContext):
    """Вход в флоу предсказания цены одной поездки

    Args:
        message (types.Message): Сообщение от пользователя
        state (FSMContext): состояние конечного автомата
    """
    answer_text = """
Введите координаты точки отправления в Нью-Йорке

Координаты можно ввести в форматах:
1. Геолокации
2. Адрес на английском языке, например: <code>127 Hudson St, New York, NY 10013, United States</code>
3. Широта и долгота через пробел в формате, например <code>40.720314 -74.008884</code>
"""
    await state.clear()
    await state.set_data({})

    await message.answer(text=answer_text, parse_mode=ParseMode.HTML)
    await state.set_state(SinglePredictionStates.pickup_point_enter)


@router.message(
    Command("single_prediction"),
)
async def flow_enter_command(message: types.Message, state: FSMContext):
    """Вход в флоу предсказания цены одной поездки через команду

    Args:
        message (types.Message): Сообщение от пользователя
        state (FSMContext): состояние конечного автомата
    """
    await flow_enter(message, state)


@router.callback_query(
    F.data == MenuButtonsData(action=MenuButtons.SINGLE_PREDICTION).pack(),
)
async def flow_enter_inline_button(
    callback_query: types.CallbackQuery | types.Message, state: FSMContext
):
    """Вход в флоу предсказания цены одной поездки через инлайн кнопку

    Args:
        message (types.Message): Сообщение от пользователя
        state (FSMContext): состояние конечного автомата
    """
    await flow_enter(callback_query.message, state)


async def get_coords_from_text(text: str) -> tuple[str, str]:
    """Обработчик для получения координат из текста
    1. Если предоставлены координаты - парсим их и возвращаем
    2. Если предоставлен адрес - обращаемся к геокодеру за координатами

    Args:
        text (str): Текст сообщения

    Returns:
        tuple[str, str]: кортеж из координат
    """
    if re.match(r"-?\d{1,2} -?\d{1,3}", text):
        return text.split(" ")

    else:
        try:
            geocoding_results = await geocode_client.get_coordinates(text)
            if not geocoding_results:
                return

            geocoding_results = sorted(
                geocoding_results, key=lambda x: x.importance, reverse=True
            )[0]

            return geocoding_results.lat, geocoding_results.lon

        except aiohttp.ClientError:
            return


async def message_dropoff_point(message: types.message, state: FSMContext):
    answer_text = """
Введите координаты точки назначения в Нью-Йорке

Координаты можно ввести в форматах:
1. Геолокации
2. Адрес на английском, например: <code>28 Avenue B, New York, NY 10009, United States</code>
3. Широта и долгота через пробел в формате, например <code>44.722350 -73.983280</code>
"""
    await message.answer(text=answer_text, parse_mode=ParseMode.HTML)
    await state.set_state(SinglePredictionStates.dropoff_point_enter)


@router.message(StateFilter(SinglePredictionStates.pickup_point_enter))
async def get_pickup_point(message: types.Message, state: FSMContext):
    """Обработчик для получения координат точки отправления

    Args:
        message (types.Message): Сообщение от пользователя
        state (FSMContext): Текущее состояние конечного автомата
    """
    if message.location:
        coords = (message.location.latitude, message.location.longitude)

    elif message.text:
        coords = await get_coords_from_text(message.text)
        if not coords:
            await flow_enter(message, state)
            return

    else:
        await flow_enter(message, state)
        return

    coords = validate_coordinates(coords)
    if not coords:
        await flow_enter(message, state)
        return

    await state.set_data(
        {
            "pickup_latitude": coords[0],
            "pickup_longitude": coords[1],
        }
    )

    await message_dropoff_point(message, state)


async def message_passenger_count(message: types.Message, state: FSMContext):
    answer_text = """Введите количество пассажиров от 1 до 6:"""

    builder = InlineKeyboardBuilder()
    for i in range(1, 7):
        builder.button(text=str(i), callback_data=f"passengers:{i}")

    await message.answer(
        text=answer_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )
    await state.set_state(SinglePredictionStates.passengers_count_enter)


@router.message(StateFilter(SinglePredictionStates.dropoff_point_enter))
async def get_dropoff_point(message: types.Message, state: FSMContext):
    """Обработчик для получения координат точки назначения

    Args:
        message (types.Message): Сообщение от пользователя
        state (FSMContext): Текущее состояние конечного автомата
    """
    if message.location:
        coords = (message.location.latitude, message.location.longitude)

    elif message.text:
        coords = await get_coords_from_text(message.text)
        if not coords:
            await message_dropoff_point(message, state)
            return

    else:
        await message_dropoff_point(message, state)
        return

    coords = validate_coordinates(coords)
    if not coords:
        await message_dropoff_point(message, state)
        return

    data = await state.get_data()
    data["dropoff_latitude"] = coords[0]
    data["dropoff_longitude"] = coords[1]

    await state.set_data(data)
    await message_passenger_count(message, state)


async def message_pickup_date(message: types.Message, state: FSMContext):
    answer_text = """Введите дату время в формате ГГГГ-ММ-ДД чч:мм:сс"""

    await message.answer(text=answer_text, parse_mode=ParseMode.HTML)
    await state.set_state(SinglePredictionStates.pickup_date_enter)


@router.callback_query(F.data.startswith("passengers"))
async def get_passenger_count(
    callback_query: types.CallbackQuery, state: FSMContext, **kwargs
):
    passenger_count = int(callback_query.data.split(":")[1])
    data = await state.get_data()
    data["passenger_count"] = passenger_count

    await state.set_data(data)
    await message_pickup_date(callback_query.message, state)


@router.message(StateFilter(SinglePredictionStates.pickup_date_enter))
async def get_pickup_date(message: types.Message, state: FSMContext):
    if not message.text:
        await message_pickup_date(message, state)
        return

    dt = validate_datetime(message.text)
    if not dt:
        await message_pickup_date(message, state)
        return

    data = await state.get_data()
    data["pickup_datetime"] = dt
    try:
        data = TaxiTravel(**data).model_dump_df()
        await message.answer(text="Готовим предсказание ⌛")
        prediction = round(predict(data)[0], 2)
        await message.answer(text=f"Цена поездки: {prediction}")

    except ValidationError as e:
        error_message = "Обнаружены ошибки:\n\n"
        for err in e.errors():
            error_message += err.get("ctx", {}).get("error") + "\n"

        await message.answer(error_message)
