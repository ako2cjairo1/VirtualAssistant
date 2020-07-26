import json
import requests
import time
import urllib
from threading import Thread

from dbhelper import DBHelper

# TOKEN = "1310031608:AAHkuLvXb_3M-PTCuVl0lbVE4ST3Gi38ceI"
# URL = "https://api.telegram.org/bot{}/".format(TOKEN)


class TelegramBot:

    def __init__(self, token):
        self.url = "https://api.telegram.org/bot{}/".format(token)
        self.db = DBHelper()
        self.db.setup()

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.url + "getUpdates"
        if offset:
            url += "?offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def handle_updates(self, updates):
        for update in updates["result"]:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            items = self.db.get_items(chat)
            if text == "/done":
                keyboard = self.build_keyboard(items)
                self.send_message("Select an item to delete", chat, keyboard)
            elif text == "/start":
                self.send_message("Welcome to your Virtual Assistant on Telegram. Send any text to me and I'll store it as an item. Send /done to remove items", chat)
            elif text.startswith("/"):
                continue
            elif text in items:
                self.db.delete_item(text, chat)
                items = self.db.get_items(chat)
                keyboard = self.build_keyboard(items)
                self.send_message("Select an item to delete", chat, keyboard)
            # else:
            #     self.db.add_item(text, chat)
            #     items = self.db.get_items(chat)
            #     message = "\n".join(items)
            #     self.send_message(message, chat)

    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    def build_keyboard(self, items):
        keyboard = [[item] for item in items]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
        return json.dumps(reply_markup)

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        url = self.url + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def main(self):
        last_update_id = None

        while True:
            updates = self.get_updates(last_update_id)
            if updates["ok"] and len(updates["result"]) > 0:
                last_update_id = self.get_last_update_id(updates) + 1

                data = updates["result"][0]
                self.handle_updates(updates)
                # print(json.dumps(updates, indent=4))
                message = f"{data['message']['from']['first_name']}: {data['message']['text']}"
                print(message)

                # chat = data["message"]["chat"]["id"]
                # self.send_message("Here's your news briefing...", chat)
                # test = input("You: ")
                # self.send_message(test, chat)
            elif not updates["ok"]:
                print(updates["description"])
            time.sleep(0.5)


if __name__ == '__main__':
    bot = TelegramBot("1310031608:AAHkuLvXb_3M-PTCuVl0lbVE4ST3Gi38ceI")
    bot.main()
