from os import getenv
from dotenv import load_dotenv

load_dotenv()

token = getenv("BOT_TOKEN")
bot_password = getenv("BOT_PASSWORD")
appmagic_login = getenv("APPMAGIC_LOGIN")
appmagic_password = getenv("APPMAGIC_PASSWORD")
