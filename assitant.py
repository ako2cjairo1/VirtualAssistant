import os
import webbrowser
import time
import sys
import requests
from random import randint
import subprocess
import warnings
import calendar
import wikipedia
from urllib.parse import quote
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
            wake_responses = ["I'm listening...",
                              f"How can I help you {self.master_name}?"]
            self.speak(wake_responses[randint(
                0, len(wake_responses) - 1)])

        def wake_assistant(listen_timeout):
            voice_data = ""

            if listen_timeout == 0:
                voice_data = self.listen_to_audio()

                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and keyword_match(voice_data, [self.assistant_name, f"Hey {self.assistant_name}"]):
                    formulate_responses(clean_voice_data(voice_data))
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
            unknown_responses = ["I'm not sure I understand.", "hmm... I didn't understand.", "Pardon me, what's that again?",
                                 "Sorry, I didn't get that. Can you restate the question?", "Hmm.. I don't have an answer for that. Is there something else I can help you with?"]
            return unknown_responses[randint(0, len(unknown_responses) - 1)]

        def ask_time(voice_data):
            time_responses = ["It's", "The time is"]
            if "in" in voice_data.lower().split(" "):
                return google(voice_data)
            else:
                return f"{time_responses[randint(0, len(time_responses) - 1)]} {dt.now().strftime('%I:%M %p')}\n"

        def google(search_keyword):
            result = ""
            if search_keyword:
                # open a web browser and show results
                webbrowser.get().open(
                    f"https://google.com/search?q={quote(search_keyword.strip())}")
                return f"Here's what i found on the web for \"{search_keyword.strip()}\". Opening your web browser...\n"

            return result

        def google_maps(location):
            result = ""
            if location:
                # open a web browser and map
                webbrowser.get().open(
                    f"https://google.nl/maps/place/{quote(location.strip())}/&amp;")
                return f"Here\'s the map location of \"{location.strip()}\". Opening your browser..."

            return result

        def wikipedia_search(wiki_keyword):
            result = ""
            if wiki_keyword:
                try:
                    return wikipedia.summary(wiki_keyword.strip(), sentences=2)

                except wikipedia.exceptions.WikipediaException:
                    if ("who" or "who's") in wiki_keyword.lower():
                        result = f"I don't know who that is but,"
                    else:
                        result = f"I don't know what that is but,"

                    return f"{result} {google(wiki_keyword.strip())}"

            return result

        def calculator(voice_data):
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
                    new_voice_data += str(w2n.word_to_num(word)
                                          ).replace(" ", "")
                    if percentage:
                        number1 = word

            if percentage:
                # evaluate percentage equation
                compute = float(eval(f"{percentage}*.01*{number1}"))

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
            if keyword_match(voice_data, [f"turn off {self.assistant_name}", f"deactivate {self.assistant_name}", f"{self.assistant_name} deactivate"]):
                self.speak("\nHappy to help! Goodbye!")
                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                exit()

            # commands to interrupt virtual assistant
            if keyword_match(voice_data, [f"{self.assistant_name} stop", f"shut up {self.assistant_name}", f"shut it {self.assistant_name}"]):
                # return immediately, and listen again for commands
                return

            if greeting_commands(voice_data):
                greeting_responses = ["very well, thanks",
                                      "I'm fine", "I'm great!", "hi", "hello"]
                self.speak(greeting_responses[randint(
                    0, len(greeting_responses) - 1)])
                # return immediately we don't need any answers below
                return

            # commands to ask for assistant's name
            if keyword_match(voice_data, ["what is your name", "what's your name"]):
                prefix = ["My name is", "I'm"]
                self.speak(
                    f"{prefix[randint(0, len(prefix) - 1)]} {self.assistant_name}.")
                # return immediately we don't need any answers below
                return

            """ remove the assistant's name in voice_data
                from this point forward of code block
                to avoid misleading data.
            """
            voice_data = clean_voice_data(voice_data)

            # commands to ask time
            if keyword_match(voice_data, ["what time is it", "what's the time", "what is the time"]):
                response_time = ask_time(voice_data)
                if response_time:
                    response_message += response_time
                    search_google = False
                    search_wiki = False

            # commands for simple math calculations
            calc = calculator(voice_data)
            if calc:
                response_message += calc
                search_google = False
                search_wiki = False

            # commands to open apps
            if keyword_match(voice_data, ["open", "show", "run"]):
                open_app_result = open_application(voice_data)
                response_message += open_app_result

            # commands to find local files and document
            if keyword_match(voice_data, ["find file", "files", "documents"]):
                response_message += find_file(voice_data)

            # commands for wikipedia
            wiki_commands = ["what is the", "who is the", "what's the",
                             "who's the", "what is", "what's", "define", "who is", "who's"]
            if search_wiki and keyword_match(voice_data, wiki_commands):
                wiki_keyword = voice_data

                for command in wiki_commands:
                    # remove the first occurance of wiki command from voice data
                    if command in voice_data.lower():
                        wiki_keyword = voice_data[(voice_data.find(
                            command) + len(command)):].strip()

                # get aswers from wikipedia
                wiki_result = wikipedia_search(wiki_keyword)

                keyword_list = wiki_keyword.lower().split(" ")
                # if answer from wikipedia contains more than 2 words
                if len(keyword_list) > 2:
                    match_count = 0
                    for word in keyword_list:
                        # and matched with context of question, return wikipedia answer
                        if word in wiki_result.lower():
                            match_count += 1
                    if match_count < 3:
                        # else, return nothing
                        wiki_result = ""

                if wiki_result:
                    response_message += wiki_result
                    # don't search into google we found answer from wikipedia
                    search_google = False

            # commands to use google maps
            google_maps_commands = ["where is", "where's",
                                    "map of", "location of", "location"]
            if search_google and keyword_match(voice_data, google_maps_commands):
                location = ""

                for command in google_maps_commands:
                    if command in voice_data.lower():
                        print(f"A. {command}:{location}")
                        location = voice_data[(
                            voice_data.find(command) + len(command)):]

                maps_response = google_maps(location)
                if maps_response:
                    response_message += maps_response
                    # don't search on google we found answers from maps
                    search_google = False

            # commands to search on google
            google_commands = ["find", "look for", "search for", "search google for", "what is the", "who is the", "what's the", "who's the", "what is", "what's",
                               "define", "who is", "who's", "where is the", "where's the", "where is", "where's", "when is the", "when's the", "when is", "when's"]
            if search_google and keyword_match(voice_data, google_commands):
                google_keyword = ""
                # remove these commands on keyword to search on google
                for command in google_commands:
                    if command in voice_data.lower():
                        google_keyword = voice_data[(
                            voice_data.lower().find(command) + len(command)):].strip()

                # search on google if we have a keyword
                if google_keyword:
                    response_message += google(google_keyword)

            if not response_message:
                # set the unknown response if no answers
                response_message = unknown_responses()

            self.speak(response_message)

        def check_connection():
            while True:
                try:
                    response = requests.get("https://www.google.com")
                    time.sleep(2)

                    # 200 means we got connection to web
                    if response.status_code == 200:
                        # execute main function
                        main()
                        break
                except Exception:
                    print(
                        "**Virtual assistant failed to initiate. No internet connection.\n")

                time.sleep(5)

        def greeting_commands(voice_data):
            if keyword_match(voice_data, [f"what is up", "what's up", "hey", "hi", "hello"]) and len(voice_data.split(" ")) < 5:
                return True
            return False

        def clean_voice_data(voice_data):
            clean_data = voice_data

            if not greeting_commands(voice_data):
                if voice_data.lower().find(self.assistant_name.lower()) > 0:
                    # remove all words starting from assistant's name
                    clean_data = voice_data[(voice_data.lower().find(
                        self.assistant_name.lower()) + len(self.assistant_name)):].strip()

                    # if assitant name's the last word in sentence
                    if len(clean_data.split(" ")) <= 1:
                        # remove only the portion of assistant's name in voice_data
                        clean_data = voice_data.replace(
                            self.assistant_name.lower(), "").strip()

            return clean_data

        """
        Main handler of virtual assistant
        """
        def main():
            print(
                f"\nVirtual assistant \"{self.assistant_name}\" is active...")
            announce_greeting = f"Hi, {self.master_name} how can i help you?"
            listen_timeout = 0

            while True:
                # handles restarting of listen timeout
                if listen_timeout == 6:
                    listen_timeout = 0

                # try to wake the assistant
                elif wake_assistant(listen_timeout):
                    listen_timeout += 1
                    # continue the loop without listening to another command
                    continue

                # handles if assistant is still listening for commands.
                if announce_greeting or listen_timeout > 0:
                    print(
                        f"{self.assistant_name}: ... (listen timeout {listen_timeout} of 5)")

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
                    print(f"{self.assistant_name}: ZzzzZz")

                announce_greeting = None

        # proceed to main() if we got internet connection
        check_connection()
