import os
import sys
from decouple import config


class Configuration:

    def __init__(self):
        self.CYAN = "\033[1;37;46m"
        self.BLACK_CYAN = "\033[22;30;46m"
        self.GREEN = "\033[1;37;42m"
        self.BLACK_GREEN = "\033[22;30;42m"
        self.RED = "\033[1;33;41m"
        self.COLOR_RESET = "\033[0;39;49m"

        self.COMMANDS_DB = config("COMMANDS_DB")

        self.ASSISTANT_DIR = config("ASSISTANT_DIR")
        self.AUDIO_FOLDER = config("AUDIO_FOLDER")
        self.FILE_DIR = config("FILE_DIR")
        self.INIT_PROJ_DIR = config("INIT_PROJ_DIR")
        self.NEWS_DIR = config("NEWS_DIR")
        self.PSE_DIR = config("PSE_DIR")
        self.UTILS_DIR = config("UTILS_DIR")

        self.DEV_PATH_DIR = config("DEV_PATH_DIR")

        self.WOLFRAM_APP_ID = config("WOLFRAM_APP_ID")

        self.TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
        self.TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")
        self.TELEGRAM_URL = config("TELEGRAM_URL")
