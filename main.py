import csv
import asyncio
import json

import undetected_chromedriver as uc

from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from seleniumwire import webdriver as webdriver_wire
from seleniumwire.utils import decode

from bs4 import BeautifulSoup
from pathlib import Path
from fake_useragent import UserAgent

from config import appmagic_password, appmagic_login


async def auth_and_get_main_page_data(url):
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')

    driver = uc.Chrome(options=options, version_main=105)
    wait = WebDriverWait(driver, 60)
    try:
        driver.get(url)

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "login-btn"))).click()
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "checkmark"))).click()

        await asyncio.sleep(.5)

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "google"))).click()

        driver.switch_to.window(driver.window_handles[1])

        wait.until(EC.visibility_of_element_located((By.ID, "identifierId"))).send_keys(appmagic_login)
        wait.until(EC.visibility_of_element_located((By.ID, "identifierNext"))).click()

        await asyncio.sleep(1)

        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='password']/div[1]/div/div[1]/input"))) \
            .send_keys(appmagic_password)
        wait.until(EC.visibility_of_element_located((By.ID, "passwordNext"))).click()

        driver.switch_to.window(driver.window_handles[0])

        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='mat-radio-24']/label"))).click()

        await asyncio.sleep(1)

        wait.until(EC.visibility_of_element_located((By.XPATH, f"/html/body/app-root/layout/div[2]/top-layout/top-apps/"
                                                               f"div/top-rows-wrap/div/div/top-apps-item[1]")))
        main_page = driver.page_source

        top_free = driver.find_element(By.CLASS_NAME, "rows-wrap").find_elements(By.CLASS_NAME, "col")[0]
        urls = [a.get_attribute("href") + "/info" for a in top_free.find_elements(By.CLASS_NAME, "g-app-name")]

        return main_page, urls
    except Exception:
        return None, None
    finally:
        driver.close()
        driver.quit()


def get_top_variables(percent_key, countries, country_codes):
    top_country = None
    top_percent = None

    top_percents = [country[percent_key] for country in countries]
    if top_percents:
        top_percent = max(top_percents)
        if top_percent != 0:
            top_country_code = countries[top_percents.index(top_percent)]["country"]
            top_percent = f"{round(top_percent, 2)}%"
            for country_code in country_codes:
                if country_code["isoCode"] == top_country_code:
                    top_country = country_code["name"]

                    break

    return top_percent, top_country


async def proceed_game(game_url, filename):
    options = ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument(f'--user-agent={UserAgent().random}')

    service = Service(executable_path=str(Path(Path().resolve(), "chromedriver.exe")))

    driver = webdriver_wire.Chrome(options=options, service=service)
    wait = WebDriverWait(driver, 120)
    try:
        driver.get(game_url)
        wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/app-root/layout/div[2]/app-page/"
                                                               "app-info-dialog/div[1]/div[3]/widgets-wrap/"
                                                               "div/div[2]/div[1]/similarity-widget")))
        await asyncio.sleep(.5)

        search_by_ids_found = False
        ltv_found = False
        data_countries_found = False

        for request in driver.requests:
            try:
                body = decode(request.response.body, request.response.headers.get("content-encoding"))
                data = json.loads(body.decode("utf-8"))["data"]
            except Exception:
                continue

            if "search-by-ids" in request.url:
                search_by_ids_found = True

                game_data = data[0]

                game_name = game_data["name"].strip()
                publisher_name = game_data["unitedPublisher"]["name"]

                downloads = game_data["downloads"]
                if downloads == 0:
                    downloads = None
                elif downloads == 1:
                    downloads = 5000

                revenue = game_data["revenue"]
                if revenue == 0:
                    revenue = None
                elif revenue == 1:
                    revenue = 5000

                art_styles = []
                setting = None
                game_tags = []

                tags = game_data["tags"]
                for tag in tags:
                    tag_type = tag["type"]
                    tag_name = tag["name"]
                    if tag_type in ["games", "meta", "apps"]:
                        game_tags.append(tag_name)
                    elif tag_type == "artstyles":
                        art_styles.append(tag_name)
                    else:
                        setting = tag_name
            elif "ltv" in request.url:
                ltv_found = True

                ltv_data = data

                ltv_west = 0
                ltv_east = 0
                ltv_global = 0

                ltvs = ltv_data
                for ltv in ltvs:
                    ltv_title = ltv["name"]
                    ltv_value = ltv["ltv"]
                    if not ltv_value:
                        ltv_value = 0

                    if ltv_title == "Tier-1 East":
                        ltv_east = round(ltv_value, 2)
                    elif ltv_title == "Tier-1 West":
                        ltv_west = round(ltv_value, 2)
                    else:
                        ltv_global = round(ltv_value, 2)
            elif "data-countries" in request.url:
                data_countries_found = True

                countries_data = data

                countries = [country_data for country_data in countries_data if country_data["country"] != "WW"]
                with open("countries.json") as file:
                    country_codes = json.load(file)

                top_download_percent, top_download_country = get_top_variables("percent_downloads", countries, country_codes)
                top_revenue_percent, top_revenue_country = get_top_variables("percent_revenue", countries, country_codes)

            if all([search_by_ids_found, data_countries_found, ltv_found]):
                break

        stores_info = await get_apps_data(driver, wait, game_name)

        with open(fr"data\{filename}", "a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(
                (
                    game_name,
                    publisher_name,
                    revenue,
                    top_revenue_country,
                    top_revenue_percent,
                    downloads,
                    top_download_country,
                    top_download_percent,
                    ltv_west,
                    ltv_east,
                    ltv_global,
                    ", ".join(game_tags),
                    setting,
                    ", ".join(art_styles),
                    *stores_info,
                    game_url
                )
            )

    except Exception:
        pass


async def get_apps_data(driver, wait, game_name):
    wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/app-root/layout/div[2]/app-page/"
                                                           "app-info-dialog/div[1]/div[3]/widgets-wrap/"
                                                           "div/div[2]/div[1]/similarity-widget")))
    await asyncio.sleep(.5)

    app_store_store_link = ""
    app_store_last_update_date = None
    app_store_rating_score = None
    app_store_amount_of_ratings = None
    google_play_store_link = ""
    google_play_last_update_date = None
    google_play_rating_score = None
    google_play_amount_of_ratings = None

    google_play_found = False
    app_store_found = False

    driver.find_element(By.XPATH, "//*[@id='mat-tab-content-0-0']/div/info/div[1]/app-info-select/div").click()
    stores = len(driver.find_element(By.CLASS_NAME, "app-info-select-wrap")
                 .find_elements(By.CLASS_NAME, "cursor-pointer"))
    for i in range(1, stores + 1):
        if google_play_found and app_store_found:
            break

        if i != 1:
            driver.find_element(By.XPATH, "//*[@id='mat-tab-content-0-0']/div/"
                                          "info/div[1]/app-info-select/div").click()

        driver.find_element(By.XPATH, f"//*[@id='mat-tab-content-0-0']/div/info/div[1]/div"
                                      f"/app-info-select-panel/div/div[{i}]").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="mat-tab-content-0-0"]/div/info/div[1]/a')))
        await asyncio.sleep(.5)

        src = driver.page_source
        app_soup = BeautifulSoup(src, "lxml")

        store_name = app_soup.find("span", class_="store-icon-name").find("span").get("title").strip().lower()
        app_name = app_soup.find("span", class_="line-height-18").get("title").strip()

        if game_name.lower()[0] == app_name.lower()[0]:
            if "google play" in store_name and not google_play_found:
                try:
                    google_play_store_link = app_soup.find("a", class_="app-link")["href"]
                except Exception:
                    pass
                try:
                    exclude_text = app_soup.find_all("div", class_="release-notes-version")[0].find(
                        "b").text.strip()
                    all_text = app_soup.find_all("div", class_="release-notes-version")[0].text.strip()

                    google_play_last_update_date = all_text.replace(exclude_text, "").strip()
                except Exception:
                    pass
                try:
                    google_play_amount_of_ratings = "".join(
                        app_soup.find("div", class_="ratings-text-bottom").find("span").text.split()[:-1])
                except Exception:
                    pass
                try:
                    google_play_rating_score = app_soup.find("div", class_="score-text").text
                except Exception:
                    pass

                google_play_found = True
            elif filter(lambda type_: type_ in store_name, ["iphone", "ipad"]) and not app_store_found:
                try:
                    app_store_store_link = app_soup.find("a", class_="app-link")["href"]
                except Exception:
                    pass
                try:
                    exclude_text = app_soup.find_all("div", class_="release-notes-version")[0] \
                        .find("b").text.strip()
                    all_text = app_soup.find_all("div", class_="release-notes-version")[0].text.strip()

                    app_store_last_update_date = all_text.replace(exclude_text, "").strip()
                except Exception:
                    pass
                try:
                    app_store_amount_of_ratings = "".join(
                        app_soup.find("div", class_="ratings-text-bottom").find("span").text.split()[:-1]
                    )
                except Exception:
                    pass
                try:
                    app_store_rating_score = app_soup.find("div", class_="score-text").text
                except Exception:
                    pass

                app_store_found = True

        await asyncio.sleep(2.5)

    return google_play_store_link, app_store_store_link, google_play_last_update_date,\
        app_store_last_update_date, google_play_rating_score, app_store_rating_score, \
        google_play_amount_of_ratings, app_store_amount_of_ratings
