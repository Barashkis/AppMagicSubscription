from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("help", "Справка"),
            types.BotCommand("check_progress", "Проверить прогресс"),
            types.BotCommand("cancel_parsing", "Отменить парсинг")
        ]
    )
