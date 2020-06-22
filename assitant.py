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
from colorama import init
from urllib.parse import quote
from datetime import datetime as dt
from time import ctime
from word2number import w2n
from tts import SpeechAssistant

FILE_DIR = "c:\\users\\dave"


class VirtualAssistant(SpeechAssistant):
    def __init__(self, masters_name, assistants_name):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name

    def activate(self):
        def keyword_match(voice_data, keywords):
            lowercase_keywords = [x.lower().strip() for x in keywords]
            if (any(map(lambda word: word.lower().strip() in voice_data, lowercase_keywords))):
                return True
            return False

        def awake_greetings():
            wake_responses = ["I'm listening...",
                              f"How can I help you {self.master_name}?"]
            self.speak(wake_responses[randint(
                0, len(wake_responses) - 1)])

        def wake_assistant(listen_timeout=1):
            voice_data = ""

            if listen_timeout == 0:
                voice_data = self.listen_to_audio()

                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and keyword_match(voice_data, [f"Hey {self.assistant_name}"]):
                    formulate_responses(clean_voice_data(voice_data))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif keyword_match(voice_data, [f"Hey {self.assistant_name}"]):
                    # announce greeting from assistant
                    awake_greetings()

                    # listen for commands
                    voice_data = self.listen_to_audio()

                    if voice_data:
                        formulate_responses(voice_data)
                    return True
            return False

        def mute_assistant(voice_data):
            # commands to interrupt virtual assistant
            if keyword_match(voice_data, [f"{self.assistant_name} stop", f"stop {self.assistant_name}", f"don't listen {self.assistant_name}", f"shut up {self.assistant_name}", f"{self.assistant_name} shut up"]):
                # don't listen for commands temporarily
                print(f"{self.assistant_name}: (muted)")
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

        def youtube(search_keyword=None):
            result = ""
            browser = webbrowser.get()
            if search_keyword and browser.open(f"https://www.youtube.com/results?search_query={quote(search_keyword.strip())}"):
                result = f"I found something on Youtube for \"{search_keyword}\"."
            elif browser.open("https://www.youtube.com/"):
                result = "Ok! opening YouTube website."
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
            answer = 0
            equation = ""

            for word in voice_data.split():
                if keyword_match(word, ["+", "plus", "add"]):
                    operator = " + "
                    equation += operator
                elif keyword_match(word, ["-", "minus", "subtract"]):
                    operator = " - "
                    equation += operator
                elif keyword_match(word, ["x", "times", "multiply", "multiply by", "multiplied by"]):
                    operator = " * "
                    equation += operator
                elif keyword_match(word, ["/", "divide", "divide by", "divided by", "divided to", "divide with"]):
                    operator = " / "
                    equation += operator
                elif keyword_match(word, ["percent", "%"]):
                    operator = "%"
                    if not word.isdigit() and "%" in word:
                        equation += f"{word} of "
                        percentage = w2n.word_to_num(word.replace("%", ""))
                    else:
                        equation += "% of "
                        percentage = number1
                    number1 = 0
                elif keyword_match(word, ["dot", "point", "."]):
                    equation += "."
                elif word.isdigit():
                    # build the equation
                    equation += str(w2n.word_to_num(word)
                                    ).replace(" ", "")
                    if percentage:
                        number1 = word

            if percentage:
                equation = f"{percentage}*.01*{number1}".replace(",", "")
                # evaluate percentage equation
                answer = float(eval(equation))

            if not answer and percentage:
                # if no computation was made, just return equivalent value of percentage
                return f"{percentage}% is {percentage * .01}"

            if not answer and equation:
                try:
                    # evaluate the equation made
                    answer = eval(equation.replace(",", ""))
                except ZeroDivisionError:
                    zero_division_responses = [
                        "The answer is somwhere between infinity, negative infinity, and undefined.", f"The answer is undefined."]
                    return zero_division_responses[randint(0, len(zero_division_responses)-1)]
                except Exception:
                    return ""

            if answer and len(str(equation).split()) > 1:
                answer_w_decimal = float('{:.02f}'.format(answer))
                # check answer for decimal places, convert to integer (whole number) if decimal places is ".00"
                format_answer = answer_w_decimal if int(
                    (str(answer_w_decimal).split('.'))[1]) > 0 else int(answer)

                return f"{equation} is {format_answer}"
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
                        return youtube()
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

        def find_file(file_name, using_explorer=True):
            response_message = ""

            if file_name:
                # find files using windows explorer
                if using_explorer:
                    # open windows explorer and look for files using queries
                    subprocess.Popen(
                        f'explorer /root,"search-ms:query=*{file_name}*&crumb=location:{FILE_DIR}&"')
                    response_message = f"Here's what I found for files with \"{file_name}\". I'm showing you the folder...\n"

                # find files using command console
                else:
                    files_found = {'(Files Found)'}
                    found_file_count = 0
                    file_count = 0

                    # confirm if the user, is looking for files/documents
                    confirm = self.listen_to_audio(
                        f"Would you me to look for files with \"{file_name}\"?")

                    if confirm.lower().strip() == "yes":
                        self.speak(
                            f"\nSearching directories for files with \"{file_name}\"")

                        try:
                            # start the file search
                            for subdir, dirs, files in os.walk(FILE_DIR):
                                for file_ in files:
                                    isFileFound = False
                                    file_count += 1

                                    if file_name.lower().strip() in str(file_).lower().strip():
                                        isFileFound = True
                                    if isFileFound:
                                        fname = ""
                                        found_file_count += 1
                                        fn = (os.path.join(
                                            subdir, file_).lower().split("\\"))[-1]
                                        fname = os.path.join(subdir, file_).lower().replace(
                                            FILE_DIR, "..").replace(fn, "")

                                        files_found.add(f"'{fname}'")

                                    # announce every 5000th file is done searched
                                    if file_count > 0 and ((file_count % 5000) == 0):
                                        print(
                                            f"{self.assistant_name}: so far, I found {found_file_count} o/f {file_count}")
                                        self.speak("Searching...")

                        except KeyboardInterrupt:
                            self.speak("Search interrupted...")

                        if found_file_count > 0:
                            # show the directories of files found
                            for fl in files_found:
                                print(fl.replace("'", "").replace(
                                    "(Files Found)", f"Files found: {found_file_count}"))

                            print(
                                f"\n----- {found_file_count} files found -----\n")
                            response_message = f"I found {found_file_count} files. I'm showing you the directories where to see them.\n"

            return response_message

        def formulate_responses(voice_data):
            response_message = ""
            search_google = True
            search_wiki = True
            use_calc = True

            # respond to wake commands
            if wake_assistant():
                # then exit immediately
                return

            # commands to terminate virtual assistant
            if keyword_match(voice_data, [f"turn off {self.assistant_name}", f"deactivate {self.assistant_name}", f"{self.assistant_name} deactivate"]):
                self.speak("\nHappy to help! Goodbye!")
                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                # terminate and end the virtual assistant application
                exit()

            # commands for greeting
            greeting_commands = [f"what is up", "what's up",
                                 "how are you", "hey", "hi", "hello"]
            greeting_responses = ["very well, thanks",
                                  "I'm fine", "I'm great!", "hi", "hello"]
            if keyword_match(voice_data, greeting_commands):
                meta_keyword = extract_metadata(
                    voice_data, greeting_commands).lower().strip()

                # if no metakeyword or if metakeyword is equal to assistant's name,
                # then, this is just a greeting
                if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                    self.speak(greeting_responses[randint(
                        0, len(greeting_responses) - 1)])
                    # return immediately, we don't need contextual answers
                    return

            # commands to ask for assistant's name
            if keyword_match(voice_data, ["what is your name", "what's your name"]):
                prefix = ["My name is", "I'm"]
                self.speak(
                    f"{prefix[randint(0, len(prefix) - 1)]} {self.assistant_name}.")
                # return immediately we don't need any answers below
                return

            # commands for confirmation
            confirmation_commands = [f"thank you {self.assistant_name}", f"thanks {self.assistant_name}", "thanks a lot", "thank you very much"
                                     f"ok {self.assistant_name}", "ok", "thank you", "thanks", "all right"]
            confirmation_responses = [
                "let me know if there's something else I can help you with.", "ok", "alright", "that's great!"]
            if keyword_match(voice_data, confirmation_commands):
                if not extract_metadata(voice_data, confirmation_commands).strip():
                    self.speak(confirmation_responses[randint(
                        0, len(confirmation_responses) - 1)])
                    # return immediately, it is a confirmation command,
                    # we don't need further contextual answers
                    return

            """ 
                Remove the assistant's name in voice_data
                from this point forward of code block
                to avoid misleading data.
            """
            voice_data = clean_voice_data(voice_data)

            # commands for controlling screen brightness
            brightness_commands = ["set the brightness to", "set brightness to", "bring up the brightness to", "bring up brightness to", "bring brightness to", "turn up the brightness to", "turn up brightness to", "turn up brightness",
                                   "change brightness to", "change brightness", "brightness by", "brightness to", "brightness"]

            # commands to control wi-fi
            wifi_commands = ["turn on the wi-fi", "turn on wi-fi",
                             "turn off the wi-fi", "turn off wi-fi"]

            # commands to control system
            system_shutdown_commands = ["shutdown system", "system shutdown",
                                        "shutdown computer", "restart system", "system restart", "restart computer"]
            if keyword_match(voice_data, (brightness_commands + wifi_commands + system_shutdown_commands)):
                system_responses = ""
                if "brightness" in voice_data:
                    brightness_percentage = screen_brightness(voice_data)
                    if brightness_percentage:
                        system_responses = f"Ok! I set the brightness by {brightness_percentage}%"
                elif "wi-fi" in voice_data:
                    system_responses = control_wifi(voice_data)
                elif ("shutdown" in voice_data) or ("restart" in voice_data):
                    system_responses = control_system(voice_data)

                if system_responses:
                    response_message += system_responses
                    use_calc = False

            # commands to ask time
            if keyword_match(voice_data, ["what time is it", "what's the time", "what is the time"]):
                response_time = ask_time(voice_data)
                if response_time:
                    response_message += response_time
                    search_google = False
                    search_wiki = False

            # commands for simple math calculations
            if use_calc:
                calc = calculator(voice_data)
                if calc:
                    response_message += calc
                    search_google = False
                    search_wiki = False

            # commands to open apps
            if keyword_match(voice_data, ["open", "show", "run"]):
                response_message += open_application(voice_data)

            # commands to find local files and document
            find_file_commands = [
                "find files of", "find file of", "files for", "files", "documents"]
            if keyword_match(voice_data, find_file_commands):
                file_keyword = extract_metadata(voice_data, find_file_commands)
                find_file_response = find_file(file_keyword)
                if find_file_response:
                    response_message += find_file_response
                    # we found response from find_fil, don't search on google or wiki
                    search_google = False
                    search_wiki = False

            # commands for wikipedia
            wiki_commands = ["what is the", "who is the", "what's the",
                             "who's the", "what is", "what's", "define", "who is", "who's"]
            if search_wiki and keyword_match(voice_data, wiki_commands):
                # extract the keyword
                wiki_keyword = extract_metadata(voice_data, wiki_commands)
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

            # commands for youtube
            youtube_commands = ["youtube video of", "youtube videos of", "youtube video",
                                "youtube videos", "find youtube", "videos of", "video of", "video about"]
            if keyword_match(voice_data, youtube_commands):
                # extract youtube keyword to search
                youtube_keyword = extract_metadata(
                    voice_data, youtube_commands)
                # search the keyword in youtube website
                youtube_response = youtube(youtube_keyword)

                # we got response from youtube, now append it to list of response_message
                if youtube_response:
                    response_message += youtube_response
                    # don't search into google we found answer from youtube
                    search_google = False

            # commands to use google maps
            google_maps_commands = ["where is", "where's",
                                    "map of", "location of", "location"]
            if search_google and keyword_match(voice_data, google_maps_commands):
                # extract the location name
                location = extract_metadata(voice_data, google_maps_commands)

                if location:
                    response_message += google_maps(location)
                    # don't search on google we found answers from maps
                    search_google = False

            # commands to search on google
            google_commands = ["find", "look for", "search for", "search google for", "what is the", "who is the", "what's the", "who's the", "what is", "what's",
                               "define", "who is", "who's", "where is the", "where's the", "where is", "where's", "when is the", "when's the", "when is", "when's"]
            if search_google and keyword_match(voice_data, google_commands):
                # remove these commands on keyword to search on google
                google_keyword = extract_metadata(voice_data, google_commands)

                # search on google if we have a keyword
                if google_keyword:
                    response_message += google(google_keyword)

            # we did not found any response
            if not response_message:
                # set the unknown response
                response_message = unknown_responses()

            # anounce all the respons(es)
            self.speak(response_message)

        def screen_brightness(voice_data):
            percentage = int([val for val in voice_data.replace(
                '%', '').split(' ') if val.isdigit()][0]) if True else 50

            # import Windows Management Instrumentation module
            import wmi
            # set the screen brightness (in percentage)
            wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[
                0].WmiSetBrightness(percentage, 0)

            return percentage

        def control_wifi(voice_data):
            command = ""
            if "on" in voice_data:
                command = "enabled"
            elif "off" in voice_data:
                command = "disabled"

            if command:
                os.system(f"netsh interface set interface \"Wi-Fi\" {command}")

                return f"Done! I {command} the wi-fi."
            return ""

        def control_system(voice_data):
            command = ""
            confirmation = "no"
            if "shutdown" in voice_data:
                # shudown command sequence
                command = "shutdown /s /t 1"

            elif "restart" in voice_data:
                # restart command sequence
                command = "shutdown /r /t 1"

            if command:
                confirmation = self.listen_to_audio(
                    f"\033[1;33;41m Want to \"{'Restart' if '/r' in command else 'Shutdown'}\" your computer? (yes/no): ")

                # execute the shutdown/restart command if confirmed by user
                if confirmation.lower().strip() == "yes":
                    os.system(command)
                    return f"Ok! {'restarting...' if '/r' in command else 'shuting down...'}"
            return ""

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
                except Exception as ex:
                    print(ex)
                    print(
                        "**Virtual assistant failed to initiate. No internet connection.\n")

                time.sleep(5)

        def clean_voice_data(voice_data):
            clean_data = voice_data

            # if not greeting_commands(voice_data):
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

        def extract_metadata(voice_data, commands):
            meta_keyword = voice_data
            extracted = True

            for command in commands:
                # remove the first occurance of command from voice data
                if command.lower().strip() in voice_data.lower():
                    extracted = False
                    meta_keyword = voice_data[(voice_data.find(
                        command.lower().strip()) + len(command)):].strip()
                    # apply recursion until we extracted the meta_data
                    return extract_metadata(meta_keyword, commands)

            if extracted:
                # # set to original voice_data if no meta_keword was found
                if not meta_keyword:
                    meta_keyword = voice_data
                return meta_keyword

        """
        Main handler of virtual assistant
        """
        def main():
            # autoreset color coding of texts to normal
            init(autoreset=True)

            loop_counter = 0
            print(
                f"\nVirtual assistant \"{self.assistant_name}\" is active...")
            announce_greeting = f"Hi, {self.master_name} how can i help you?"
            listen_timeout = 0

            while True:
                loop_counter += 1
                # handles restarting of listen timeout
                if listen_timeout >= 6:
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

                    # mute command is activated, stop listening
                    if mute_assistant(voice_data):
                        listen_timeout = 10
                        # start the loop again and wait for "wake commands"
                        continue

                    if voice_data:
                        formulate_responses(voice_data)
                        # deduct listen timeout
                        if 1 < listen_timeout <= 5:
                            listen_timeout -= 1
                            continue

                    listen_timeout += 1

                else:
                    if (loop_counter <= 1) or ((loop_counter % 20) == 0):
                        # every 20th cycle, show if assistant is sleeping (muted).
                        print(f"{self.assistant_name}: ZzzzZz")

                    if loop_counter == 100:
                        # reset loop counter every 100th cycle
                        loop_counter = 0

                announce_greeting = None

        # check internet connectivity
        # before proceeding to main()
        check_connection()
