import os
import webbrowser
import time
import sys
from random import randint
import subprocess
import warnings
import calendar
import wikipedia
from datetime import datetime as dt
from time import ctime
from word2number import w2n
from tts import SpeechAssistant


class VirtualAssistant(SpeechAssistant):
    def __init__(self, masters_name, assistants_name):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name

    def activate(self):
        def keyword_match(voice_data, keywords):
            lowercase_keywords = [x.lower() for x in keywords]
            if (any(map(lambda word: word.lower() in voice_data, lowercase_keywords))):
                return True
            return False

        def awake_greetings():
            wake_responses = ["Yup. I'm listening...",
                              f"How can I help you {self.master_name}?"]
            self.speak(wake_responses[randint(
                0, len(wake_responses) - 1)])

        def wake_assistant(listen_timeout):
            voice_data = ""

            if listen_timeout == 0:
                voice_data = self.listen_to_audio()

                # wake command is invoked and the user ask immediately.
                if len(voice_data.split(" ")) > 2 and keyword_match(voice_data, [self.assistant_name, f"Hey {self.assistant_name}"]):

                    # remove the wake commands and the rest of voice_data will be use to formulate a response
                    clean_voice_data = voice_data.lower().replace(f"hey {self.assistant_name.lower()}", "").replace(
                        f"{self.assistant_name.lower()}", "").strip()

                    formulate_responses(clean_voice_data)
                    return True

                # wake commands is invoked and expected to ask for another command
                elif keyword_match(voice_data, [self.assistant_name, f"Hey {self.assistant_name}"]):
                    # announce greeting from assistant
                    awake_greetings()

                    # listen for commands
                    voice_data = self.listen_to_audio()

                    if voice_data:
                        formulate_responses(voice_data)
                    return True
            return False

        def unknown_responses():
            unknown_responses = ["hmmm... I didn't quite get that",
                                 "Sorry! I didn't get that..."]
            return unknown_responses[randint(0, len(unknown_responses) - 1)]

        def ask_time(voice_data):
            time_responses = ["It's", "The time is"]
            if "in" in voice_data.lower().split(" "):
                return search_on_google(voice_data)
            else:
                return f"{time_responses[randint(0, len(time_responses) - 1)]} {dt.now().strftime('%I:%M %p')}\n"

        def search_on_google(search_keyword):
            url = "https://google.com/search?q=" + search_keyword.strip()

            # open a web browser and show results
            webbrowser.get().open(url)
            return f"Here's what i found on the web for \"{search_keyword.strip()}\". Opening your web browser...\n"

        def google_maps(location):
            url = "https://google.nl/maps/place/" + location.strip() + "/&amp;"
            webbrowser.get().open(url)
            return f"Here\'s the map location of {location.strip()}\n"

        def search_on_wiki(wiki_keyword):
            if wiki_keyword:
                try:
                    return wikipedia.summary(wiki_keyword.strip(), sentences=2)
                except wikipedia.exceptions.WikipediaException as e:
                    print(f"{e}\n")
                    return f"I don't know who that is. But, {search_on_google(wiki_keyword.strip())}"

            return ""

        def simple_calculation(voice_data):
            operator = ""
            number1 = 0
            percentage = 0
            compute = 0
            new_voice_data = ""

            for word in voice_data.split():
                if keyword_match(word, ["+", "plus", "add"]):
                    operator = " + "
                    new_voice_data += operator
                elif keyword_match(word, ["-", "minus", "subtract"]):
                    operator = " - "
                    new_voice_data += operator
                elif keyword_match(word, ["x", "times", "multiply", "multiplied"]):
                    operator = " * "
                    new_voice_data += operator
                elif keyword_match(word, ["/", "divide", "divided"]):
                    operator = " / "
                    new_voice_data += operator
                elif keyword_match(word, ["percent", "%"]):
                    operator = "%"
                    if not word.isdigit() and "%" in word:
                        new_voice_data += f"{word} of "
                        percentage = w2n.word_to_num(word.replace("%", ""))
                    else:
                        new_voice_data += "% of "
                        percentage = number1
                    number1 = 0
                elif word.isdigit():
                    # build the equation
                    new_voice_data += str(w2n.word_to_num(word))
                    if percentage:
                        number1 = word

            if percentage:
                # evaluate percentage equation
                compute = float(eval(f"{percentage} * .01 * {number1}"))

            if not compute and percentage:
                # if no computation was made, just return equivalent value of percentage
                return f"{percentage}% is {percentage * .01}"
            if not compute and new_voice_data:
                try:
                    # evaluate the equation made
                    compute = eval(new_voice_data)
                except ZeroDivisionError:
                    zero_division_responses = [
                        "The answer is somwhere between infinity, negative infinity, and undefined.", f"The answer is undefined."]
                    return zero_division_responses[randint(0, len(zero_division_responses)-1)]
                except Exception:
                    return ""

            if compute and len(str(new_voice_data).split()) > 1:
                return "".join([new_voice_data, f" is {'{0:.3g}'.format(compute)}"])
            else:
                return ""

        def open_application(voice_data):
            confirmation = ""

            if keyword_match(voice_data, ["vs code", "visual studio code"]):
                confirmation = "Ok! opening Visual Studio Code"
                subprocess.call(
                    "C:/Users/Dave/AppData/Local/Programs/Microsoft VS Code/Code.exe")

            elif keyword_match(voice_data, ["youtube", "netflix", "github", "facebook", "twitter", "instagram"]):
                for web_app in voice_data.lower().split(" "):
                    url = ""
                    if web_app == "youtube" and web_app in voice_data:
                        url = "https://www.youtube.com/"
                    elif web_app == "netflix" and web_app in voice_data:
                        url = "https://www.netflix.com/ph/"
                    elif web_app == "github" and web_app in voice_data:
                        url = "https://github.com"
                    elif web_app == "facebook" and web_app in voice_data:
                        url = "https://www.facebook.com"
                    elif web_app == "twitter" and web_app in voice_data:
                        url = "https://twitter.com"
                    elif web_app == "instagram" and web_app in voice_data:
                        url = "https://www.instagram.com"

                    # open the webapp in web browser
                    if url:
                        webbrowser.get().open(url)
                confirmation = "Ok! opening in your browser."

            return confirmation

        def find_file(voice_data):
            response_message = ""
            file_count = 0
            file = ""

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

        def formulate_responses(voice_data):
            response_message = ""
            search_google = True
            search_wiki = True

            # commands to terminate virtual assistant
            if keyword_match(voice_data, ["shut up", f"close {self.assistant_name}", f"turn off {self.assistant_name}"]):
                self.speak("\nHappy to help! Goodbye!")
                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                exit()

            # ask assistants name
            if keyword_match(voice_data, ["what is your name", "what's your name"]):
                prefix = ["My name is", "I'm"]
                response_message = f"{prefix[randint(0,len(prefix) - 1)]} {self.assistant_name}.\n"
                search_google = False
                search_wiki = False

            # ask time
            if keyword_match(voice_data, ["what time is it", "what's the time", "what is the time"]):
                response_time = ask_time(voice_data)
                if response_time:
                    response_message += response_time
                    search_google = False
                    search_wiki = False

            # use wikipedia
            wiki_commands = ["what's", "who's", "who is",
                             "define", "what is", "what is the", "what's the"]
            if search_wiki and keyword_match(voice_data, wiki_commands):
                wiki_keyword = voice_data
                for command in wiki_commands:
                    wiki_keyword = wiki_keyword.replace(command, "").strip()

                wiki_result = search_on_wiki(wiki_keyword)

                # if wiki_keyword contains more than 2 words
                # and matched with voice_data, return the wiki_result
                # else, return blank string value
                keyword_list = wiki_keyword.split(" ")
                if len(keyword_list) > 2:
                    match_count = 0
                    for word in keyword_list:
                        # should contain words from voice_data
                        if word in wiki_result.lower():
                            match_count += 1
                    if match_count < 3:
                        wiki_result = ""

                if wiki_result:
                    response_message += wiki_result

            # commands for simple math calculations
            calc = simple_calculation(voice_data)
            if calc:
                response_message += calc
                search_google = False

            # commands to open apps
            if keyword_match(voice_data, ["open", "show", "run"]):
                response_message += open_application(voice_data)

            # commands to find local files and document
            if keyword_match(voice_data, ["find file", "files", "documents"]):
                response_message += find_file(voice_data)

            # commands to use google maps
            if search_google and keyword_match(voice_data, ["where is", "map of", "location"]):
                voice_data_list = voice_data.split(" ")
                location = ""

                if "where is" in voice_data:
                    location = voice_data[(
                        voice_data.find("where is") + 8):].strip()
                elif "map of" in voice_data:
                    location = voice_data[(
                        voice_data.find("map of") + 6):].strip()
                elif "location" in voice_data_list:
                    location = voice_data[(
                        voice_data.find("location") + 8):].strip()
                response_message += google_maps(location)

            # commands to search on google
            if search_google and keyword_match(voice_data, ["find", "define", "what's", "what is", "what is the", "what's the", "look for", "search for", "search google for"]):
                voice_data_list = voice_data.split(" ")
                voice_data.replace("on google", "").replace("into google", "")
                search_keyword = ""

                if "find" in voice_data_list:
                    search_keyword = voice_data[(voice_data.find(
                        "find") + 4):].strip()
                elif "define" in voice_data_list:
                    search_keyword = voice_data[(voice_data.find(
                        "define") + 6):].strip()
                elif "what's the" in voice_data:
                    search_keyword = voice_data[(
                        voice_data.find("what's the") + 10):].strip()
                elif "what is the" in voice_data:
                    search_keyword = voice_data[(
                        voice_data.find("what is the") + 11):].strip()
                elif "what is" in voice_data:
                    search_keyword = voice_data[(
                        voice_data.find("what is") + 7):].strip()
                elif "look for" in voice_data:
                    search_keyword = voice_data[(voice_data.find(
                        "look for") + 8):].strip()
                elif "search for" in voice_data:
                    search_keyword = voice_data[(voice_data.find(
                        "search for") + 10):].strip()
                elif "search google for" in voice_data:
                    search_keyword = voice_data[(voice_data.find(
                        "search google for") + 17):].strip()
                elif "search google" in voice_data:
                    search_keyword = voice_data[(voice_data.find(
                        "search google") + 13):].strip()
                response_message += search_on_google(search_keyword)

            if not response_message:
                response_message = unknown_responses()

            self.speak(response_message)

        """
        Main handler of virtual assistant
        """
        print(f"\n{self.assistant_name} assistant is ACTIVE...")
        announce_greeting = f"Hi, how can i help you {self.master_name}?"
        listen_timeout = 0

        while True:
            # handles restarting of listen timeout
            if listen_timeout == 5:
                listen_timeout = 0

            # try to wake the assistant
            elif wake_assistant(listen_timeout):
                listen_timeout += 1
                print(f"Listening...{listen_timeout}")
                # continue the loop without listening to another command
                continue

            # handles if assistant is still listening for commands.
            if announce_greeting or listen_timeout > 0:
                print(f"Listening...{listen_timeout}")
                # listen for commands
                voice_data = self.listen_to_audio(announce_greeting)

                if voice_data:
                    formulate_responses(voice_data)
                    # deduct listen timeout
                    if 1 < listen_timeout <= 5:
                        listen_timeout -= 1
                        continue

                listen_timeout += 1
            else:
                print(f"\nSleeping...{listen_timeout}")

            announce_greeting = None
