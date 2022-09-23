from aiogram import executor

from handlers import dp
from utils import set_default_commands


async def on_startup(_):
    await set_default_commands(dp)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
