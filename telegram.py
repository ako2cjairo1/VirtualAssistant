import json
import requests
import time
import urllib
from threading import Event
from settings import Configuration
from datetime import datetime


class TelegramBot(Configuration):

    def __init__(self):
        super().__init__()
        self.url = f"{self.TELEGRAM_URL}{self.TELEGRAM_TOKEN}/"
        self.last_update_id = None
        self.last_command = ""
        self.botId = datetime.now().strftime('%I:%M:%S')
        self.bot_isAlive = False
        self.ping = False
        self.telegram_event = Event()

    def get_url(self, url):
        try:
            response = requests.get(url)
            return response.content.decode("utf8")

        except Exception:
            pass
            # print(f"[BOT] Error while parsing URL.")
            self.kill_telegram_events()

    def get_json_from_url(self, url):
        try:
            content = self.get_url(url)
            return json.loads(content)

        except Exception:
            pass
            # print(
            #     f"[BOT] Error while parsing JSON from response.")
            self.kill_telegram_events()

    def get_updates(self, offset=None):
        try:
            url = self.url + "getUpdates"
            if offset:
                url += f"?offset={offset}"
            return self.get_json_from_url(url)
        except Exception:
            self.kill_telegram_events()
            # print(f"[BOT] Error while pulling updates.")
            pass

    def get_last_update_id(self, updates):
        update_ids = []
        try:
            for update in updates["result"]:
                update_ids.append(int(update["update_id"]))
            return max(update_ids)
        except Exception:
            self.kill_telegram_events()
            # print(
            #     f"[BOT] Error while pulling the last update id.")
            pass

    def get_last_chat_text(self, updates):
        try:
            num_updates = len(updates["result"])
            last_update = num_updates - 1
            message = updates["result"][last_update]["message"]["text"]
            return message

        except Exception:
            pass
            # print(
            #     f"[BOT] Error while pulling the last chat message.")
            self.kill_telegram_events()

    def send_message(self, text, reply_markup=None):
        try:
            text = urllib.parse.quote_plus(text)
            url = self.url + \
                f"sendMessage?text={text}&chat_id={self.TELEGRAM_CHAT_ID}"  # &parse_mode=Markdown"

            if reply_markup:
                url += f"&reply_markup={reply_markup}"

            self.get_url(url)

        except Exception:
            pass
            # print(f"[BOT] Error while sending message.")
            self.kill_telegram_events()

    def refresh_poll(self):
        try:
            self.ping = False
            time.sleep(5)

            if self.ping:
                return True
            else:
                self.kill_telegram_events()
                return False

        except Exception:
            pass
            print(f"[BOT] Error while refresh polling..")
            self.kill_telegram_events()

    def kill_telegram_events(self):
        self.bot_isAlive = False
        if self.telegram_event:
            self.telegram_event.set()

    def poll(self):
        try:
            # let continue this polling every half a second
            while not self.telegram_event.is_set():
                self.bot_isAlive = True
                self.ping = True

                # let's pull the latest update in chat
                updates = self.get_updates(self.last_update_id)

                # print(f"{self.botId}")

                if updates == None: self.kill_telegram_events()
                # if successful update and must have result count
                if updates and updates["ok"] and len(updates["result"]) > 0:
                    # increment update_id based from the last update index
                    self.last_update_id = self.get_last_update_id(updates) + 1

                    command = self.get_last_chat_text(updates)
                    if "--start" in command.lower() or "/start" in command.lower():
                        command = ""
                        self.send_message(
                            "Welcome to your personal Virtual Assistant on Telegram. Send some questions/commands to me and I'll try my best to respond.")
                    self.last_command = command.strip().lower()

                time.sleep(0.3)

        except Exception as ex:
            pass
            self.kill_telegram_events()
            raise Exception(f"[BOT] Error polling bot, trying again... {ex}")
