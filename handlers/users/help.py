from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandHelp
from aiogram.utils.markdown import hbold

from loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_allowed = data.get("is_allowed")
    if is_allowed:
        await message.answer("Чтобы бот начал парсить игры, необходимо ему отправить ссылку "
                             f"или ссылки ({hbold('через пробел')}) на топ игр. Сначала бот проведет их валидацию, "
                             "а затем начнет парсинг. Извлечение информации о 1000 играх "
                             "проходит примерно в течение 5 часов\n\n"
                             "Важно отметить, что если кто-то запустил парсинг, другие люди не могут его запустить, "
                             "необходимо подождать")
    else:
        await message.answer("Чтобы пользоваться ботом, нужно войти в него. Чтобы это сделать, введите команду /start")
