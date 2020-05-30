import os
import webbrowser
import time
import sys
import random
import subprocess
import warnings
import calendar
import wikipedia
from time import ctime
from word2number import w2n
import tts


class YuriResponse:
    def search_keywords(self, voice_data, keywords):
        lowercase_keywords = [x.lower() for x in keywords]
        if (any(map(lambda word: word in voice_data, lowercase_keywords))):
            return True
        return False

    def wake_yuri(self, listenCount):
        voice_data = tts.listen_to_audio()
        if (1 <= listenCount <= 2):
            return True
        elif self.search_keywords(voice_data, ["Yuri", "Hey Yuri"]):
            wake_responses = ["I'm listening...", "How can I help you?"]
            tts.speak(wake_responses[random.randint(
                0, len(wake_responses) - 1)])
            return True
        return False

    def unknown_response(self):
        unknown_responses = ["hmmm... I didn't quite get that",
                             "Sorry! I didn't get that..."]
        return unknown_responses[random.randint(0, len(unknown_responses) - 1)]

    def search_person_name(self, voice_data):
        if "who is" in voice_data:
            words_list = voice_data.split()

            for i in range(0, len(words_list)-1):
                if len(words_list) >= 3 and words_list[i].lower() == "who" and words_list[i+1].lower() == "is":
                    person_name = words_list[i+2] + \
                        f" {words_list[i+3]}" if len(words_list) > 3 else ""
                    return wikipedia.summary(person_name, sentences=2)
        return ""

    # This needs to be further evaluated

    def simple_calculation(self, voice_data):
        operator = ""
        number1 = 0
        number2 = 0
        percentage = 0
        compute = 0
        new_voice_data = ""
        success = False
        for word in voice_data.split():
            if self.search_keywords(voice_data, ["+", "plus", "add"]):
                operator = " + "
                new_voice_data += operator
            elif self.search_keywords(voice_data, ["-", "minus", "subtract"]):
                operator = " - "
                new_voice_data += operator
            elif self.search_keywords(voice_data, ["x", "times", "multiply", "multiplied"]):
                operator = "*"
                new_voice_data += " x "
            elif self.search_keywords(voice_data, ["/", "divide", "divided"]):
                operator = " / "
                new_voice_data += operator
            elif self.search_keywords(voice_data, ["percent", "%"]):
                operator = "%"
                if not word.isdigit() and "%" in word:
                    new_voice_data += f"{word} of "
                    percentage = w2n.word_to_num(word.replace('%', ''))
                else:
                    new_voice_data += "% of "
                    percentage = number1
                number1 = 0
            elif word.isdigit():
                new_voice_data += str(w2n.word_to_num(word))
                if number1 == 0:
                    number1 = w2n.word_to_num(word)
                else:
                    number2 = w2n.word_to_num(word)
                    if "+" in operator:
                        compute = number1 + number2
                    elif "-" in operator:
                        compute = number1 - number2
                    elif "*" in operator:
                        compute = number1 * number2
                    elif "/" in operator:
                        compute = number1 / number2
                    number1 = compute
                    number2 = 0

        if percentage:
            compute = (percentage * .01) * number1
        if not compute and percentage:
            return f"{percentage}% is {percentage * .01}"
        if not compute:
            return ""

        new_voice_data += f" is {'{0:.3g}'.format(compute)}"

        return new_voice_data

    def open_application(self, voice_data):
        if self.search_keywords(voice_data, ["open", "run"]):
            if self.search_keywords(voice_data, ["vs code", "visual studio code"]):
                tts.speak("Ok! opening Visual Studio Code")
                subprocess.call(
                    "C:/Users/Dave/AppData/Local/Programs/Microsoft VS Code/Code.exe")

    def find_file(self, voice_data):
        response_message = ""
        file_count = 0
        file = ""
        if self.search_keywords(voice_data, ["find file", "find", "files", "documents"]):
            for subdir, dirs, files in os.walk("C:/Users/Dave"):
                for file_ in files:
                    isFileFound = False
                    words = voice_data.split()
                    if (len(words) > 2 and words[1] == "file") and words[2] == str(file_):
                        isFileFound = True
                    elif words[1] == str(file_):
                        isFileFound = True
                        # os.system(
                        #     f"explorer search-ms:query={words[1]}&crumb=location:c:\\Users\\Dave")
                    if isFileFound:
                        file_count += 1
                        file = os.path.join(subdir, file_)
                        print(file)
                        response_message += file + "\n"
            if response_message:
                response_message += f"----- {file_count} files found -----"
        return response_message

    def formulate_responses(self, voice_data):
        response_message = ""
        if self.search_keywords(voice_data, ["what is your name", "what's your name"]):
            response_message = "My name is Yuri. "

        if self.search_keywords(voice_data, ["what time is it", "what's the time", "what is the time"]):
            response_message += f"The time is {ctime()} \n"

        if self.search_keywords(voice_data, ["where is", "map", "location"]):
            location = tts.listen_to_audio("What is the location?")
            url = "https://google.nl/maps/place/" + location + "/&amp;"
            webbrowser.get().open(url)
            response_message += f"Here\'s the map location of {location}\n"

        response_message += self.search_person_name(voice_data) if True else ""

        response_message += self.simple_calculation(voice_data) if True else ""

        self.open_application(voice_data)

        response_message += self.find_file(voice_data)

        if self.search_keywords(voice_data, ["define", "look for"]):
            search = tts.listen_to_audio("What do you wanna search for?")
            url = "https://google.com/search?q=" + search
            webbrowser.get().open(url)
            response_message += f"Here\'s what I found in browser for {search}\n"

        if self.search_keywords(voice_data, ["shut up", "close Yuri", "turn off yuri"]):
            exit()

        if not response_message:
            response_message = self.unknown_response()

        tts.speak(response_message)
