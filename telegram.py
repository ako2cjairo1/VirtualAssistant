import json
import requests
import time
import urllib
from threading import Thread
from settings import Configuration


class TelegramBot(Configuration):

    def __init__(self):
        super().__init__()
        self.url = f"{self.TELEGRAM_URL}{self.TELEGRAM_TOKEN}/"
        self.last_update_id = None
        self.last_command = None

    def get_url(self, url):
        try:
            response = requests.get(url)
            return response.content.decode("utf8")

        except Exception as ex:
            raise Exception(f"Error while parsing URL. {str(ex)}")

    def get_json_from_url(self, url):
        try:
            content = self.get_url(url)
            return json.loads(content)

        except Exception as ex:
            raise Exception(f"Error while parsing JSON from response. {str(ex)}")

    def get_updates(self, offset=None):
        try:
            url = self.url + "getUpdates"
            if offset:
                url += f"?offset={offset}"
            return self.get_json_from_url(url)
        except Exception as ex:
            raise Exception(f"Error while pulling updates. {str(ex)}")

    def get_last_update_id(self, updates):
        update_ids = []
        try:
            for update in updates["result"]:
                update_ids.append(int(update["update_id"]))
            return max(update_ids)
        except Exception as ex:
            raise Exception(f"Error while pulling the last update id. {str(ex)}")

    def get_last_chat_text(self, updates):
        try:
            num_updates = len(updates["result"])
            last_update = num_updates - 1
            return updates["result"][last_update]["message"]["text"]

        except Exception as ex:
            raise Exception(f"Error while pulling the last chat message. {str(ex)}")

    def send_message(self, text, reply_markup=None):
        try:
            text = urllib.parse.quote_plus(text)
            url = self.url + f"sendMessage?text={text}&chat_id={self.TELEGRAM_CHAT_ID}&parse_mode=Markdown"

            if reply_markup:
                url += f"&reply_markup={reply_markup}"

            self.get_url(url)

        except Exception as ex:
            raise Exception(f"Error while sending message. {str(ex)}")

    def poll(self):
        try:
            # let continue this polling every half a second
            while True:
                # let's pull the latest update in chat
                updates = self.get_updates(self.last_update_id)

                # if successul update and must have result count
                if updates["ok"] and len(updates["result"]) > 0:
                    # increment update_id based from the last update index
                    self.last_update_id = self.get_last_update_id(updates) + 1

                    command = self.get_last_chat_text(updates)
                    if command == "/start":
                        self.send_message("Welcome to your personal Virtual Assistant on Telegram. Send some questions/commands to me and I'll try my best to respond.")

                    self.last_command = command.strip().lower()

                time.sleep(0.5)

        except Exception:
            raise Exception(f"Error polling bot, trying to poll again...")
