import asyncio
import csv
import os
from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import Update
from aiogram.dispatcher.filters.builtin import Command

from main import auth_and_get_main_page_data, proceed_game

from loader import dp

in_process = False


@dp.message_handler(Command("check_progress"))
async def check_progress(message: types.Message, state: FSMContext):
    global in_process

    data = await state.get_data()
    is_allowed = data.get("is_allowed")
    is_process_of_user = data.get("in_process")
    if is_allowed:
        if is_process_of_user:
            data = await state.get_data()

            total_games = data.get("total_games")
            current_url = data.get("current_url")
            current_game = data.get("current_game")

            await message.answer(f"Обработано игр: {current_game}/{total_games}, ссылка номер {current_url}")
        elif in_process:
            await message.answer("Уже кто-то запустил парсинг...")
        else:
            await message.answer("Вы еще не запускали парсинг...")
    else:
        await message.answer("Чтобы пользоваться ботом, нужно войти в него. Чтобы это сделать, введите команду /start")


@dp.message_handler(Command("cancel_parsing"))
async def cancel_parsing(message: types.Message, state: FSMContext):
    global in_process

    data = await state.get_data()
    is_allowed = data.get("is_allowed")
    is_process_of_user = data.get("in_process")
    if is_allowed:
        if is_process_of_user:
            in_process = False
            async with state.proxy() as data:
                data["in_process"] = False

            await message.answer("Отменяю парсинг...")
        elif in_process:
            await message.answer("Уже кто-то запустил парсинг...")
        else:
            await message.answer("Вы еще не запускали парсинг...")
    else:
        await message.answer("Чтобы пользоваться ботом, нужно войти в него. Чтобы это сделать, введите команду /start")


@dp.message_handler()
async def parse_appmagic_games(message: types.Message, state: FSMContext):
    global in_process

    data = await state.get_data()
    is_allowed = data.get("is_allowed")
    is_process_of_user = data.get("in_process")
    if is_allowed:
        if not in_process:
            urls = message.text.strip().split()
            uris_for_all_urls = []

            in_process = True
            async with state.proxy() as data:
                data["in_process"] = True

            await message.answer("Провожу валидацию... Валидация одной ссылки может занять до 2 минут")
            for url in urls:
                main_page, game_urls = await auth_and_get_main_page_data(url)

                if main_page is None or game_urls is None:
                    in_process = False
                    async with state.proxy() as data:
                        data["in_process"] = False

                    await message.answer("Валидация одной из ссылок прошла неудачно. Пожалуйста, "
                                         f"повторите попытку\n\nСсылка, не прошедшая валидацию: {url}")

                    return
                else:
                    uris_for_all_urls.append(game_urls)

            await message.answer("Валидация прошла успешно. Приступаю к извлечению данных... Чтобы узнать прогресс, "
                                 "введите команду /check_progress")

            in_process = True
            async with state.proxy() as data:
                data["in_process"] = True
                data["total_games"] = 0
                data["current_game"] = 0
                data["current_url"] = 0

            if not os.path.exists("data"):
                os.mkdir("data")

            filename = f"parse-{datetime.now().strftime('%d.%m.%Y')}-{datetime.now().strftime('%H.%M')}.csv"
            with open(fr"data\{filename}", "w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(
                    (
                        "Game name",
                        "Publisher name",
                        "Revenue",
                        "Top revenue country",
                        "Top percent of the revenue",
                        "Downloads",
                        "Top downloads country",
                        "Top percent downloads",
                        "LTV Tier 1 West",
                        "LTV Tier 1 East",
                        "LTV Global",
                        "Tags",
                        "Setting",
                        "Artstyle",
                        "Store Link – Google Play",
                        "Store Link – Apple Store iPhone",
                        "Last update date – Google Play",
                        "Last update date – Apple Store iPhone",
                        "Rating score – Google Play",
                        "Rating score – Apple Store iPhone",
                        "Amount of ratings – Google Play",
                        "Amount of ratings – Apple Store iPhone",
                        "Appmagic link"
                    )
                )

            for url_count in range(1, len(urls) + 1):
                async with state.proxy() as data:
                    data["current_url"] += 1

                game_urls = uris_for_all_urls[url_count - 1]

                async with state.proxy() as data:
                    data["total_games"] = len(game_urls)

                games_count = 0
                for game_url in game_urls:
                    if not in_process:
                        os.remove(fr"data\{filename}")
                        await message.answer("Парсинг отменен")

                        return

                    await proceed_game(game_url, filename)

                    async with state.proxy() as data:
                        data["current_game"] += 1

                    games_count += 1
                    if games_count % 10 == 0:
                        await asyncio.sleep(30)

                    await asyncio.sleep(.5)

                if url_count != len(urls):
                    await asyncio.sleep(300)

                async with state.proxy() as data:
                    data["current_game"] = 0

            await message.answer_document(open(rf"data\{filename}", "rb"))

            in_process = False
            async with state.proxy() as data:
                data["in_process"] = False
        elif is_process_of_user:
            await message.answer("Вы уже запустили парсинг")
        else:
            await message.answer("Уже кто-то запустил парсинг...")
    else:
        await message.answer("Чтобы пользоваться ботом, нужно войти в него. Чтобы это сделать, введите команду /start")


@dp.errors_handler()
async def catch_errors(update: Update, exception):
    global in_process

    if isinstance(exception, Exception):
        in_process = False
        async with dp.current_state().proxy() as data:
            data["in_process"] = False

        await update.get_current().message.answer("В процессе работы возникла ошибка... Пожалуйста, проверьте ссылки и "
                                                  "повторите попытку")
