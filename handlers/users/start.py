from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart

from loader import dp

from config import bot_password


@dp.message_handler(CommandStart())
async def start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_allowed = data.get("is_allowed")
    if is_allowed:
        await message.answer(f"Приветствую, {message.from_user.full_name}!\n\n"
                             "Это бот для парсинга игр на сайте AppMagic. Для поучения справки о том, как "
                             "им пользоваться, введите команду /help")
    else:
        await message.answer("Введите пароль")
        await state.set_state("password")


@dp.message_handler(state="password")
async def auth(message: types.Message, state: FSMContext):
    password_from_user = message.text.strip()
    if password_from_user == bot_password:
        await state.reset_state()
        async with state.proxy() as data:
            data["is_allowed"] = True

        await message.answer(f"Приветствую, {message.from_user.full_name}!\n\n"
                             "Это бот для парсинга игр на сайте AppMagic. Для поучения справки о том, как "
                             "им пользоваться, введите команду /help")
    else:
        await message.answer("Пароль неверный. Повторите попытку")
