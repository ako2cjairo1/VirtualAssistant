import json
import requests
import time
import urllib
from threading import Thread


class TelegramBot:

    def __init__(self, token, chat_id):
        self.url = "https://api.telegram.org/bot{}/".format(token)
        self.last_update_id = None
        self.chat_id = chat_id
        self.last_command = None

    def get_url(self, url):
        content = ""
        try:
            response = requests.get(url)
            content = response.content.decode("utf8")
            return content
        except Exception as ex:
            raise Exception(f"Error while parsing URL. {str(ex)}")

    def get_json_from_url(self, url):
        js = ""
        try:
            content = self.get_url(url)
            js = json.loads(content)
            return js
        except Exception as ex:
            raise Exception(f"Error while parsing JSON from response. {str(ex)}")

    def get_updates(self, offset=None):
        js = ""
        try:
            url = self.url + "getUpdates"
            if offset:
                url += "?offset={}".format(offset)
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
        text = ""
        try:
            num_updates = len(updates["result"])
            last_update = num_updates - 1
            return updates["result"][last_update]["message"]["text"]
            # chat_id = updates["result"][last_update]["message"]["chat"]["id"]
            # return (text, chat_id)
        except Exception as ex:
            raise Exception(f"Error while pulling the last chat message. {str(ex)}")

    def send_message(self, text, reply_markup=None):
        try:
            text = urllib.parse.quote_plus(text)
            url = self.url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, self.chat_id)

            if reply_markup:
                url += "&reply_markup={}".format(reply_markup)

            self.get_url(url)

            # let's pull the latest update in chat
            updates = self.get_updates(self.last_update_id)
            # if successul update and must have result count
            if updates["ok"] and len(updates["result"]) > 0:
                # increment update_id based from the last update index
                self.last_update_id = self.get_last_update_id(updates) + 1

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

                # elif updates["ok"] and len(updates["result"]) <= 0:
                #     print(f"NO UPDATE: {self.last_update_id}")
                # else:
                #     print(f"UNKNOWN POLL UPDATE: {self.last_update_id}")

                time.sleep(0.5)

        except Exception as ex:
            raise Exception(f"Error while polling. {str(ex)}")
