import os
import requests
import subprocess
import webbrowser
import wikipedia
import wolframalpha
import time
import wmi  # (screen brightness) Windows Management Instrumentation module
import logging
import concurrent.futures as task
from threading import Thread
from helper import displayException, is_match, get_commands, clean_voice_data, extract_metadata, execute_map
from urllib.parse import quote
from random import choice
from datetime import datetime as dt
from word2number import w2n

FILE_DIR = "c:\\users\\dave"
VIRTUAL_ASSISTANT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\VirtualAssistant"
UTILITIES_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\PythonUtilityProjects"
INIT_PROJECT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\ProjectGitInitAutomation"
PSE_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\PSE"
NEWS_SCRAPER_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\NewsScraper"
DEV_PATH_DIR = os.environ.get("DevPath")
WOLFRAM_APP_ID = os.environ.get("WOLFRAM_APP_ID")


class SkillsLibrary:

    def __init__(self, tts, masters_name, assistants_name):
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.tts = tts

    def print(self, message):
        print(message)

        message = message.replace(f"{self.assistant_name}:", "")
        self.tts.respond_to_bot(message)

    def _get_commands(self, command_name):
        return get_commands(command_name, self.assistant_name, self.master_name)

    def ask_time(self, voice_data):
        if "in" in voice_data.lower().split(" "):
            return ""
        else:
            time_prefix = ["It's", "The time is"]
            return f'{choice(time_prefix)} {dt.now().strftime("%I:%M %p")}'

    def google(self, search_keyword):
        result = ""
        # open google iste in web browser and show results
        if search_keyword:
            link = f"https://google.com/search?q={quote(search_keyword.strip())}"

            open_browser_thread = Thread(target=execute_map, args=("open browser", [link],))
            open_browser_thread.setDaemon(True)
            open_browser_thread.start()
            result = f"Here's what I found on the web for \"{search_keyword.strip()}\". Opening your web browser...\n"

            # let get the redirected url (if possible) from link we have
            redirect_url = requests.get(link)
            # send the link to bot
            self.tts.respond_to_bot(redirect_url.url)

        return result

    def youtube(self, search_keyword=None):
        result = ""
        # open youtube site in web browser and show results
        if search_keyword:
            link = f"https://www.youtube.com/results?search_query={quote(search_keyword.strip())}"

            open_browser_thread = Thread(target=execute_map, args=("open browser", [link],))
            open_browser_thread.setDaemon(True)
            open_browser_thread.start()
            result = f"I found something on Youtube for \"{search_keyword}\"."

            # send the link to bot
            self.tts.respond_to_bot(link)

        return result

    def google_maps(self, location):
        result = ""
        if location:
            link = f"https://google.nl/maps/place/{quote(location.strip())}/&amp;"
            # open a web browser and map
            open_browser_thread = Thread(target=execute_map, args=("open browser", [link],))
            open_browser_thread.setDaemon(True)
            open_browser_thread.start()
            result = f"Here\'s the map location of \"{location.strip()}\". Opening your browser..."

            # let get the redirected url (if possible) from link we have
            redirect_url = requests.get(link)
            # send the link to bot
            self.tts.respond_to_bot(redirect_url.url)

        return result

    def wolfram_search(self, voice_data):
        response = ""
        meta_data = ""
        parts_of_speech = self._get_commands("parts of speech")

        try:
            client = wolframalpha.Client(WOLFRAM_APP_ID)

            def _resolveListOrDict(value):
                if isinstance(value, list):
                    return value[0]["plaintext"]
                else:
                    return value["plaintext"]

            def _removeBrackets(value):
                if value:
                    return value.replace("|", "").strip().split("(")[0].replace("  ", " ")
                else:
                    return ""

            def _weatherReport(data):
                report = ""
                try:
                    max_temp = ""
                    min_temp = ""
                    ave_temp = ""
                    conditions = []
                    current_hour = int(dt.now().strftime("%I"))
                    current_meridian_indicator = dt.now().strftime("%p")
                    time_frame = "morning" if ("AM" == current_meridian_indicator and current_hour <= 10) else ("afternoon" if (("AM" == current_meridian_indicator and current_hour > 10) or (
                        "PM" == current_meridian_indicator and current_hour == 12) or ("PM" == current_meridian_indicator and current_hour <= 2)) else "night")

                    data = data.replace('rain', 'raining').replace(
                        'few clouds', 'cloudy').replace("clear", "clear skies")

                    for item in data.split("\n"):
                        if "°C" in item:
                            temps = item.replace("between", "").replace(
                                "°C", "").split("and")

                            if len(temps) > 1:
                                min_temp = temps[0].strip()
                                max_temp = temps[1].strip()
                                ave_temp = str(
                                    (int(max_temp) + int(min_temp)) // 2)
                            else:
                                ave_temp = item.replace("°C", "").strip()

                        elif is_match(item, ["|"]):
                            for cond in item.split("|"):
                                if time_frame == "morning" and "early morning" in cond:
                                    if "(" in cond:
                                        conditions.append(
                                            cond[:cond.index("(")].strip())
                                elif time_frame == "afternoon" and "afternoon" in cond:
                                    if "(" in cond:
                                        conditions.append(
                                            cond[:cond.index("(")].strip())
                                elif "(" in cond:
                                    conditions.append(
                                        cond[:cond.index("(")].strip())
                                # conditions.append(cond.strip())

                            if max_temp and min_temp:
                                if len(conditions) > 2:
                                    report = f"{conditions[0]} and {ave_temp}°C. Expect mixed conditions starting {time_frame} and the rest of the day. Temperatures are heading down from {max_temp}°C to {min_temp}°C."
                                else:
                                    report = f"{conditions[0]} and {ave_temp}°C. Expect {' and '.join(conditions)} starting {time_frame} with mixed conditions for the rest of the day. Temperatures are heading down from {max_temp}°C to {min_temp}°C."
                            else:
                                conditions = ' and '.join(conditions)
                                report = f"{ave_temp}°C with mixed condition like {conditions}."
                        else:
                            conditions = item.strip()
                            report = f"{conditions} and {ave_temp}°C."

                except Exception:
                    pass
                    displayException("Wolfram|Alpha Weather Report Error.")

                return report

            weather_commands = self._get_commands("weather")
            report_type = "weather forecast"
            current_location = "Malolos, Bulacan"
            is_weather_report = False

            if is_match(voice_data, weather_commands):
                meta_data = extract_metadata(
                    voice_data, (["in", "on", "for", "this"] + weather_commands)).replace("forecast", "")

                if is_match(voice_data, ["rain", "precipitation"]):
                    report_type = "rain forecast"
                elif is_match(voice_data, ["temperature"]):
                    report_type = "temperature"

                # let's build the query for weather, temperature or precipitation forecast.
                # this will be our parameter input in Wolfram API
                if is_match(voice_data, ["in", "on", "for", "this"]):
                    if meta_data:
                        voice_data = f"{report_type} for {meta_data}"
                    else:
                        voice_data = f"{report_type} for {current_location}"
                else:
                    meta_data = extract_metadata(voice_data, weather_commands)
                    voice_data = f"{report_type} for {current_location} {meta_data}"
                is_weather_report = True

            # send query to Wolfram Alpha
            wolframAlpha = client.query(voice_data)

            # check if we have a successful result
            if wolframAlpha["@success"] == "true":
                # may contain extracted question or query meta data
                pod0 = wolframAlpha["pod"][0]

                # may contain the answer
                pod1 = wolframAlpha["pod"][1]

                # extracting wolfram question interpretation from pod0
                question = _resolveListOrDict(pod0["subpod"])

                # removing unnecessary parenthesis
                question = _removeBrackets(question).strip()

                # checking if pod1 has primary=true or title=result|definition
                if (("definition" in pod1["@title"].lower()) or ("result" in pod1["@title"].lower()) or (pod1.get("@primary", "false") == "true")):

                    # extract result from pod1
                    wolfram_response = _resolveListOrDict(pod1["subpod"])

                    # if no answers found return a blank response
                    if (wolfram_response is None) or is_match(wolfram_response, ["(data not available)", "(no data available)", "(unknown)"]):
                        return ""

                    # create a weather report
                    if is_weather_report:
                        # rain forecast (precipitation)
                        if "precipitation" in question:
                            precipitation_forecast = ""

                            if "rain" in wolfram_response:
                                precipitation_forecast = choice(
                                    [f"The forecast calls for {wolfram_response} for{question}", f"Yes, I think we'll see some {wolfram_response} for {question}"])
                            else:
                                precipitation_forecast = choice(
                                    [f"It doesn't look like it's going to {wolfram_response} for{question}", f"I don't believe it will {wolfram_response} for {question}"]).replace("no precipitation", "rain")
                            return precipitation_forecast.replace("precipitation forecast", "").replace("rain\n", "rain on ")

                        # weather and temperature forecast
                        report_heading = "Here's the " + question.replace("temperature", "temperature for").replace(
                            "weather forecast", "weather forecast for").replace("\n", ", ")
                        report_prefix = "It's currently"

                        if report_type == "weather forecast":
                            wolfram_response = _weatherReport(wolfram_response)

                        if is_match(meta_data, self._get_commands("time and day")):
                            report_prefix = f"{meta_data.capitalize()} will be"

                        return f"{report_heading}. \n\n{report_prefix} {wolfram_response}"

                    # remove "according to" phrase in wolfram response
                    if is_match(wolfram_response, ["(according to"]):
                        wolfram_response = wolfram_response.split(
                            "(according to")[0]

                    if is_match(wolfram_response, ["I was created by"]):
                        wolfram_response = f"I was created by {self.master_name}."

                    wolfram_meta = wolfram_response.split("|")

                    # replace "Q:" and "A:" prefixes and replace new space instead
                    if is_match(wolfram_response, ["Q: ", "A: "]) or is_match(question, ["tell me a joke."]):
                        response = wolfram_response.replace(
                            "Q: ", "").replace("A: ", "\n\n")

                    # we found an array of information, let's disect if necessary
                    elif wolfram_response.count("|") > 2:
                        if is_match(wolfram_response, parts_of_speech):
                            # responding to definition of terms, and using the first answer in the list as definition
                            response = f"\"{question}\" \n. ({wolfram_meta[1]}) . \nIt means... {wolfram_meta[-1].strip().capitalize()}."
                        else:
                            # respond by showing list of information
                            self.tts.speak("Here's some information.")

                            for deet in wolfram_response.split(" | "):
                                self.print(f">> {deet}.")
                            print("\n")

                            return "success"

                    # we found an array of information, let's disect if necessary
                    elif wolfram_response.count("\n") > 3:
                        # respond by showing list of information
                        self.tts.speak("Here's some information.")

                        for deet in wolfram_response.split("\n"):
                            self.print(f">> {deet}.")
                        print("\n")

                        return "success"

                    # we found at least 1 set of defition, disect further if necessary
                    elif is_match(wolfram_response, ["|"]):
                        # extract the 12 hour time value
                        if is_match(voice_data, ["time"]):

                            # check for 12 hour time value
                            if len(wolfram_response.split(":")[0]) == 2:
                                hour = wolfram_response[:5]
                                ampm = wolfram_response[9:11]
                                response = f"{hour} {ampm}"
                            else:
                                hour = wolfram_response[:4]
                                ampm = wolfram_response[8:10]
                                response = f"{hour} {ampm}"

                        # responding to "do you know my name?"
                        elif is_match(wolfram_response, ["my name is"]):
                            # replace "Wolfram|Aplha" to assistant's name.
                            response = wolfram_response[:(wolfram_response.lower().find(
                                "my name is") + 11)] + self.assistant_name + ". Are you " + self.master_name + "?"

                        else:
                            # responding to definition of terms
                            if is_match(wolfram_response, parts_of_speech):
                                response = f"\"{question}\" \n. ({wolfram_meta[0]}) . \nIt means... {wolfram_meta[-1].strip().capitalize()}."
                            else:
                                response = wolfram_response

                    # single string response
                    else:
                        if is_match(voice_data, ["how do you spell", "spell", "spelling", "spells"]):

                            question = question.replace(
                                "spellings", "").strip()
                            if len(wolfram_response) > len(question):
                                # there are one or more word spelling, we need to figure out which one is in question.
                                word_found = False
                                for word in wolfram_response.split(" "):
                                    if word.lower() in voice_data.lower().split(" "):
                                        question = word
                                        wolfram_response = word
                                        word_found = True
                                        break

                                # if we don't find the word to spell in wolfram response, then it must be the "question"
                                if not word_found:
                                    wolfram_response = question

                            # let's split the letters of response to simulate spelling the word(s).
                            response = f'{question}\n\n . {" . ".join(list(wolfram_response.capitalize()))}'
                        else:
                            if "happy birthday to you." in question.lower():
                                response = wolfram_response.replace(
                                    "<fill in name of birthday person>", self.master_name)
                            elif wolfram_response.isdigit():
                                numeric_response = wolfram_response
                                if "date" not in question.lower():
                                    numeric_response = "{:,}".format(
                                        int(wolfram_response))

                                # response = f"{question} is {numeric_response}"
                                response = numeric_response
                            else:
                                response = wolfram_response

                    parts_of_speech.append("Here's some information.")
                    # don't include the evaluated question in result if it has "?", "here's some information" or more than 5 words in it
                    if len(voice_data.split(" ")) > 5 or is_match(voice_data, ["how do you spell", "spell", "spelling", "spells"]) or is_match(question, ["?", "tell me a joke.", "thank you.", "happy birthday to you."]) or is_match(response, parts_of_speech):
                        return response
                    else:
                        if question:
                            return f"{question} is {response}."
                        else:
                            return f"{question} {response}."

        except Exception:
            pass
            displayException("Wolfram|Alpha Search Skill Error.")

        # if no answers found return a blank response
        return response

    def wikipedia_search(self, wiki_keyword, voice_data):
        result = ""
        if wiki_keyword:
            try:
                summary = wikipedia.summary(wiki_keyword.strip(), sentences=2)
                if len(summary.split(" ")) > 30 or len(summary.split(".")[0].split(" ")) > 30:
                    summary = summary.split(".")[0] + "."

                return summary

            except wikipedia.exceptions.WikipediaException:
                displayException(
                    "Wikipedia Search Skill (handled)", logging.INFO)

                if ("who" or "who's") in voice_data.lower():
                    result = "I don't know who that is but,"
                else:
                    result = "I don't know what that is but,"

                return f"{result} {self.google(wiki_keyword.strip())}"

            except Exception:
                displayException("Wikipedia Search Skill Error.")

        return result

    def calculator(self, voice_data):
        operator = ""
        number1 = 0
        percentage = 0
        answer = None
        equation = ""

        # evaluate if there are square root or cube root questions, replace with single word
        evaluated_voice_data = voice_data.replace(",", "").replace("power of", "power#of").replace(
            "square root", "square#root").replace("cube root", "cube#root").split(" ")

        try:
            for word in evaluated_voice_data:
                if is_match(word, ["+", "plus", "add"]):
                    operator = " + " if not word.replace("+",
                                                         "").isdigit() else word
                    equation += operator
                elif is_match(word, ["-", "minus", "subtract"]):
                    operator = " - " if not word.replace("-",
                                                         "").isdigit() else word
                    equation += operator
                elif is_match(word, ["x", "times", "multiply", "multiplied"]):
                    operator = " * "
                    equation += operator
                elif is_match(word, ["/", "divide", "divided"]):
                    operator = " / "
                    equation += operator
                elif is_match(word, ["^", "power#of"]):
                    operator = " ^ "
                    equation += operator
                elif is_match(word, ["square#root"]):
                    equation += "x2"
                elif is_match(word, ["cube#root"]):
                    equation += "x3"
                elif is_match(word, ["percent", "%"]):
                    operator = "%"
                    if not word.isdigit() and "%" in word:
                        equation += f"{word} of "
                        percentage = w2n.word_to_num(word.replace("%", ""))
                    else:
                        equation += "% of "
                        percentage = number1
                    number1 = 0
                elif is_match(word, ["dot", "point", "."]):
                    equation += word

                # try to convert words to numbers
                elif word.isdigit() or is_match(word, ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero"]):
                    # build the equation
                    equation += str(w2n.word_to_num(word)).replace(" ", "")

                    # store number value for special equations (percentage, square root, cube root)
                    if percentage or ("x2" in equation) or ("x3" in equation):
                        number1 = word

            if percentage and int(number1) > 0:
                equation = f"{percentage}*.01*{number1}"
                # evaluate percentage equation
                answer = float(eval(equation))
                # create a readable equation
                equation = f"{percentage}% of {number1}"

            # no percentage computation was made,
            # just return equivalent value of percent
            if (answer is None) and percentage:
                return f"{percentage}% is {percentage * .01}"

            if "x2" in equation:
                equation = f"{number1}**(1./2.)"
            elif "x3" in equation:
                equation = f"{number1}**(1./3.)"
            elif "^" in equation:
                # can't evaluate
                return ""

            if (answer is None) and equation:
                try:
                    # evaluate the equation made
                    answer = eval(equation.replace(",", ""))
                except ZeroDivisionError:
                    return choice(["The answer is somwhere between infinity, negative infinity, and undefined.", "The answer is undefined."])
                except Exception:
                    displayException(
                        "Calculator Skill Exception (handled).", logging.INFO)
                    return ""

            if answer is not None:
                with_decimal_point = float('{:.02f}'.format(answer))

                # check answer for decimal places,
                # convert to whole number if decimal point value is ".00"
                positive_float = int(
                    (str(with_decimal_point).split('.'))[1]) > 0

                format_answer = with_decimal_point if positive_float else int(
                    answer)

                # bring back the readable format of square root and cube root
                equation = equation.replace(f"{number1}**(1./2.)", f"square root of {number1}").replace(
                    f"{number1}**(1./3.)", f"cube root of {number1}")

                equation = [equation, "The answer"]

                return f"{choice(equation)} is {'approximately ' if positive_float else ''}{format_answer}"
            else:
                return ""

        except Exception:
            displayException("Calculator Skill Error.")

    def open_application(self, voice_data):
        confirmation = ""
        app_names = []
        app_commands = []
        urls = []

        def modified_app_names():
            clean_app_names = voice_data
            special_app_names = ["vs code", "sublime text", "wi-fi manager", "wi-fi monitoring", "ms code", "ms vc", "microsoft excel", "spread sheet", "ms excel", "microsoft word", "ms word", "microsoft powerpoint", "ms powerpoint", "task scheduler",
                                 "visual studio code", "pse ticker", "command console", "command prompt", "control panel", "task manager", "resource monitor", "resource manager", "device manager", "windows services", "remove programs", "add remove"]
            for name in special_app_names:
                if name in voice_data:
                    # make one word app name by using hyphen
                    clean_app_names = clean_app_names.replace(
                        name, name.replace(" ", "-"))

            # return unique list of words/app names
            return {word for word in clean_app_names.split(" ")}

        try:
            for app in modified_app_names():
                if is_match(app, ["explorer", "folder"]):
                    app_commands.append(
                        "start explorer C:\\Users\\Dave\\DEVENV\\Python")
                    app_names.append("Windows Explorer")

                elif is_match(app, ["control-panel"]):
                    app_commands.append("start control")
                    app_names.append("Control Panel")

                elif is_match(app, ["device-manager", "device"]):
                    app_commands.append("start devmgmt.msc")
                    app_names.append("Device Manager")

                elif is_match(app, ["windows-services", "services"]):
                    app_commands.append("start services.msc")
                    app_names.append("Windows Services")

                elif is_match(app, ["add-remove-program", "remove-programs", "add-remove", "unistall"]):
                    app_commands.append("start control appwiz.cpl")
                    app_names.append("Programs and Features")

                elif is_match(app, ["resource-manager", "resource-monitor"]):
                    app_commands.append("start resmon")
                    app_names.append("Resource Manager")

                elif is_match(app, ["task-manager"]):
                    app_commands.append("start Taskmgr")
                    app_names.append("Task Manager")

                elif is_match(app, ["task-scheduler", "scheduler"]):
                    app_commands.append("start taskschd.msc")
                    app_names.append("Task Scheduler")

                elif is_match(app, ["notepad", "textpad", "notes"]):
                    app_commands.append("start notepad")
                    app_names.append("Notepad")

                elif is_match(app, ["calculator"]):
                    app_commands.append("start calc")
                    app_names.append("Calculator")

                elif is_match(app, ["command-console", "command-prompt", "terminal", "command"]):
                    app_commands.append("start cmd")
                    app_names.append("Command Console")

                elif is_match(app, ["microsoft-excel", "ms-excel", "excel", "spread-sheet"]):
                    app_commands.append("start excel")
                    app_names.append("Microsoft Excel")

                elif is_match(app, ["microsoft-word", "ms-word", "word"]):
                    app_commands.append("start winword")
                    app_names.append("Microsoft Word")

                elif is_match(app, ["microsoft-powerpoint", "ms-powerpoint", "powerpoint"]):
                    app_commands.append("start winword")
                    app_names.append("Microsoft Powerpoint")

                elif is_match(app, ["spotify"]):
                    app_commands.append(
                        "C:\\Users\\Dave\\AppData\\Roaming\\Spotify\\Spotify.exe")
                    app_names.append("Spotify")

                elif is_match(app, ["vscode", "vs-code", "ms-code", "ms-vc", "visual-studio-code"]):
                    app_commands.append("start code -n")
                    app_names.append("Visual Studio Code")

                elif is_match(app, ["sublime", "sublime-text"]):
                    app_commands.append("start sublime_text -n")
                    app_names.append("Sublime Text 3")

                elif is_match(app, ["newsfeed", "news"]):
                    app_names.append("Newsfeed Ticker")
                    # change directory to NewsTicker library
                    os.chdir(NEWS_SCRAPER_MODULE_DIR)
                    # execute batch file that will open Newsfeed on a newo console window
                    os.system('start cmd /k \"start News Ticker.bat\"')
                    # get back to virtual assistant directory after command execution
                    os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

                elif is_match(app, ["wi-fi-monitoring", "wi-fi-manager"]):
                    app_names.append("Wi-Fi Manager")
                    # change directory to Wi-Fi manager library
                    os.chdir(UTILITIES_MODULE_DIR)
                    # execute batch file that will open Wi-Fi manager on a newo console window
                    os.system('start cmd /k \"wifi manager.bat\"')
                    # get back to virtual assistant directory after command execution
                    os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

                elif is_match(app, ["pse-ticker", "pse"]):
                    app_names.append("Philippine Stock Exchange Ticker")
                    # change directory to PSE library resides
                    os.chdir(PSE_MODULE_DIR)
                    # open PSE ticker in new window
                    os.system('start cmd /k \"start_PSE.bat\"')
                    # get back to virtual assistant directory after command execution
                    os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

                elif is_match(app, ["youtube", "google", "netflix", "github", "facebook", "twitter", "instagram", "wikipedia"]):
                    if app == "youtube":
                        app_names.append("Youtube")
                        urls.append("https://www.youtube.com/")
                    elif app == "google":
                        app_names.append("Google")
                        urls.append("https://www.google.com/")
                    elif app == "netflix":
                        app_names.append("Netflix")
                        urls.append("https://www.netflix.com/ph/")
                    elif app == "github":
                        urls.append("https://www.github.com")
                        app_names.append("Github")
                    elif app == "facebook":
                        urls.append("https://www.facebook.com")
                        app_names.append("Facebook")
                    elif app == "twitter":
                        urls.append("https://www.twitter.com")
                        app_names.append("Twitter")
                    elif app == "instagram":
                        urls.append("https://www.instagram.com")
                        app_names.append("Instagram")
                    elif app == "wikipedia":
                        urls.append("https://www.wikipedia.org")
                        app_names.append("Wikipedia")

            # launch local applications using python's os.system class
            if len(app_commands) > 0:
                open_app_thread = Thread(
                    target=execute_map, args=("open system", app_commands,))
                open_app_thread.setDaemon(True)
                open_app_thread.start()

            # open the webapp in web browser
            if len(urls) > 0:
                open_browser_thread = Thread(
                    target=execute_map, args=("open browser", urls,))
                open_browser_thread.setDaemon(True)
                open_browser_thread.start()
                # send the links to bot
                with task.ThreadPoolExecutor() as exec:
                    exec.map(self.tts.respond_to_bot, urls)

            if len(app_names) > 0:
                alternate_responses = self._get_commands("acknowledge response")
                confirmation = f"Ok! opening {' and '.join(app_names)}..."
                alternate_responses.append(confirmation)
                confirmation = choice(alternate_responses)

        except Exception:
            displayException("Open Application Skill Error.", logging.DEBUG)

        return confirmation

    def find_file(self, file_name, using_explorer=True):
        response_message = ""

        try:
            if file_name:
                # find files using windows explorer
                if using_explorer:
                    # open windows explorer and look for files using queries
                    explorer = f'explorer /root,"search-ms:query=name:{file_name}&crumb=location:{FILE_DIR}&"'
                    subprocess.Popen(explorer, shell=False, stdin=None,
                                     stdout=None, stderr=None, close_fds=False)
                    response_message = f"Here's what I found for files with \"{file_name}\". I'm showing you the folder...\n"

                # find files using command console
                else:
                    files_found = {'(Files Found)'}
                    found_file_count = 0
                    file_count = 0

                    # confirm if the user, is looking for files/documents
                    confirm = self.tts.listen_to_audio(
                        f"Would you me to look for files with \"{file_name}\"?")

                    if confirm.lower().strip() == "yes":
                        self.tts.speak(
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
                                        self.print(
                                            f"{self.assistant_name}: so far, I found {found_file_count} o/f {file_count}")
                                        self.tts.speak("Searching...")

                        except KeyboardInterrupt as ex:
                            displayException(
                                "Find File Skill Keyboard Interrupt (handled)", logging.INFO)
                            self.tts.speak("Search interrupted...")

                        if found_file_count > 0:
                            # show the directories of files found
                            for fl in files_found:
                                self.print(fl.replace("'", "").replace(
                                    "(Files Found)", f"Files found: {found_file_count}"))

                            self.print(
                                f"\n----- {found_file_count} files found -----\n")
                            response_message = f"I found {found_file_count} files. I'm showing you the directories where to see them.\n"
        except Exception:
            displayException("Find File Skill Error.")

        return response_message

    def screen_brightness(self, voice_data):
        try:
            percentage = int([val for val in voice_data.replace(
                '%', '').split(' ') if val.isdigit()][0]) if True else 50
            # set the screen brightness (in percentage)
            wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[
                0].WmiSetBrightness(percentage, 0)

            alternate_responses = self._get_commands("acknowledge response")
            return f"{choice(alternate_responses)} I set the brightness by {percentage}%"

        except Exception:
            displayException("Screen Brightness Skill Error.")

    def control_wifi(self, voice_data):
        command = ""
        try:
            if is_match(voice_data, ["on", "open", "enable"]):
                # if "on" in voice_data or "open" in voice_data:
                command = "enabled"
            if is_match(voice_data, ["off", "close", "disable"]):
                # elif "off" in voice_data or "close" in voice_data:
                command = "disabled"

            if command:
                os.system(f"netsh interface set interface \"Wi-Fi\" {command}")

                if "disabled" in command:
                    # announce before going off-line
                    self.print(f"\033[1;33;41m {self.assistant_name} is Offline...")

                alternate_responses = self._get_commands("acknowledge response")
                return f"{choice(alternate_responses)} I {command} the Wi-Fi."

        except Exception:
            displayException("Wi-Fi Skill Error.")

        return ""

    def control_system(self, voice_data):
        command = ""
        confirmation = "no"

        try:
            if "shutdown" in voice_data:
                # shudown command sequence for 15 seconds
                command = "shutdown /s /t 15"

            elif is_match(voice_data, ["restart", "reboot"]):
                # restart command sequence for 15 seconds
                command = "shutdown /r /t 15"

            if command:
                # confirmation = self.tts.listen_to_audio(f"\033[1;33;41m Are you sure to \"{'Restart' if '/r' in command else 'Shutdown'}\" your computer? (yes/no): ")

                # execute the shutdown/restart command if confirmed by user
                # if "yes" in confirmation.lower().strip():
                os.system(command)
                return f"Ok! {'Reboot' if '/r' in command else 'Shutdown'} sequence will commence in approximately 10 seconds..."
                # return f"{'Reboot' if '/r' in command else 'Shutdown'} is canceled."

        except Exception:
            displayException("Shutdown/Restart System Skill Error.")

        return ""

    def wallpaper(self):
        try:
            import sys
            sys.path.append(UTILITIES_MODULE_DIR)
            from wallpaper import Wallpaper

            wp = Wallpaper()
            wp.change_wallpaper()

            alternate_responses = self._get_commands("acknowledge response")
            return f"{choice(alternate_responses)} I changed your wallpaper..."

        except Exception:
            displayException("Wallpaper Skill Error.")

    def initiate_new_project(self, lang="Python", proj_name="NewPythonProject", mode="g"):
        # navigate to the ProjectGitInitAutomation directory - contains the libraries
        # to automate creation of project, it pushes the initial commit files to Github if possible
        os.chdir(INIT_PROJECT_MODULE_DIR)
        # batch file to execute project initiation in new window
        os.system(f'start cmd /k \"create.bat\" {lang} {proj_name} {mode}')
        # get back to virtual assistant directory after command execution
        os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)
        return f"The new {lang} project should open in Visual Studio Code when done..."

    def play_music(self, voice_data):
        songWasFound = False
        option = '"play all"'
        shuffle = "True"
        mode = "compact"
        title = "none"
        artist = "none"
        genre = "none"
        response = ""

        try:
            import sys
            sys.path.append(UTILITIES_MODULE_DIR)
            from musicplayer import MusicPlayer
            mp = MusicPlayer()

            # change the directory to location of batch file to execute
            os.chdir(UTILITIES_MODULE_DIR)

            music_word_found = True if is_match(
                voice_data, ["music", "songs"]) else False
            meta_data = voice_data.lower().replace("&", "and").replace(
                "music", "").replace("songs", "").strip()

            if meta_data == "":
                # mode = "compact"
                alternate_responses = self._get_commands("acknowledge response")
                response = f"{choice(alternate_responses)} Playing all songs{', shuffled' if shuffle == 'True' else '...'}"
                songWasFound = True

            elif meta_data and "by" in meta_data.split(" ") and meta_data.find("by") > 0 and len(meta_data.split()) >= 3:
                option = '"play by"'

                by_idx = meta_data.find("by")
                title = meta_data[:(by_idx - 1)].strip().capitalize()
                artist = meta_data[(by_idx + 3):].strip().capitalize()

                if mp.search_song_by(title, artist, title):
                    songWasFound = True
                    artist = f'"{artist}"'
                    genre = title

                    alternate_responses = self._get_commands("acknowledge response")
                    response = f"{choice(alternate_responses)} Playing \"{title}\" by {artist}..."
                else:
                    response = f"I couldn't find \"{title}\" in your music."

            elif meta_data:
                option = '"play by"'
                title = f'"{meta_data}"'
                artist = f'"{meta_data}"'
                genre = f'"{meta_data}"'

                mp.title = meta_data
                mp.artist = meta_data
                mp.genre = meta_data

                if mp.search_song_by(meta_data, meta_data, meta_data):
                    songWasFound = True
                    alternate_responses = self._get_commands("acknowledge response")
                    response = f"{choice(alternate_responses)} Now playing \"{meta_data.capitalize()}\" {'music...' if music_word_found else '...'}"
                else:
                    response = f"I couldn't find \"{meta_data.capitalize()}\" in your music."

            if songWasFound:
                mp.terminate_player()
                # batch file to play some music in new window
                os.system(
                    f'start cmd /k "play_some_music.bat {option} {shuffle} {mode} {title} {artist} {genre}"')

            # get back to virtual assistant directory
            os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

            return response

        except Exception:
            displayException("Play Music Skill Error.")

    def music_volume(self, volume):

        try:
            import sys
            sys.path.append(UTILITIES_MODULE_DIR)
            from musicplayer import MusicPlayer
            mp = MusicPlayer()
            # change the directory to location of batch file to execute
            os.chdir(UTILITIES_MODULE_DIR)

            mp.music_player_volume(volume)

            # get back to virtual assistant directory
            os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

        except Exception:
            displayException("Music Volume Skill Error.")

    def news_scraper(self):

        try:
            import sys
            sys.path.append(NEWS_SCRAPER_MODULE_DIR)
            from NewsScraper import NewsTicker

            # change the directory to location of batch file to execute
            os.chdir(NEWS_SCRAPER_MODULE_DIR)
            news = NewsTicker()

            # execute daemon to fetch breaking news in background
            news.fetch_news()
            news.run_breaking_news_daemon()

            # get back to virtual assistant directory
            os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

            return news

        except Exception:
            displayException("News Scraper Skill Error.")
            return None

    def toast_notification(self, title, message, duration=600):

        try:
            import sys
            sys.path.append(UTILITIES_MODULE_DIR)
            from send_toast import ToastMessage
            notification = ToastMessage()
            # change the directory to location of batch file to execute
            os.chdir(UTILITIES_MODULE_DIR)

            notification.send_toast(title, message, duration=duration)
            self.tts.respond_to_bot(f"‼️ {title} ‼️")
            self.tts.respond_to_bot(message)

            # get back to virtual assistant directory
            os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

        except Exception:
            displayException("Toast Notification Skill Error.")

    def fun_holiday(self):
        try:
            import sys
            sys.path.append(NEWS_SCRAPER_MODULE_DIR)
            from FunHolidays import FunHoliday
            fh = FunHoliday()
            # change the directory to location of batch file to execute
            os.chdir(NEWS_SCRAPER_MODULE_DIR)

            result = fh.get_fun_holiday()
            if result["success"] == "true":
                holiday = result["holiday"]

                title = f'Today is \"{holiday["title"]}\"'
                message = holiday["heading"]

                self.toast_notification(title, message, duration=300)
                self.tts.respond_to_bot(title)
                self.tts.respond_to_bot(message)
                # print(f'Date: {holiday["date"]}\nTitle: {holiday["title"]}\nHeading: {holiday["heading"]}\nDid You Know? {holiday["did you know"]}\nURL: {holiday["source url"]}')

            # get back to virtual assistant directory
            os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

        except Exception:
            displayException("Fun Holiday Skill Error.")

    def system_volume(self, vol):
        # get back to virtual assistant directory after command execution
        os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)
        # execute batch file that will open Newsfeed on a newo console window
        os.system(f'start cmd /k "set_system_volume.bat {vol}"')
