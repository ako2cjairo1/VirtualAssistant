import os
import requests
import subprocess
import webbrowser
import wikipedia
import wmi  # (screen brightness) Windows Management Instrumentation module
from helper import is_match
from urllib.parse import quote
from random import randint
from datetime import datetime as dt
from word2number import w2n
# from tts import SpeechAssistant

FILE_DIR = "c:\\users\\dave"


class ControlLibrary:
    def __init__(self, tts, assistants_name):
        self.assistant_name = assistants_name
        self.tts = tts

    def ask_time(self, voice_data):
        time_responses = ["It's", "The time is"]
        if "in" in voice_data.lower().split(" "):
            return self.google(voice_data)
        else:
            return f"{time_responses[randint(0, len(time_responses) - 1)]} {dt.now().strftime('%I:%M %p')}\n"

    def google(self, search_keyword):
        result = ""
        if search_keyword:
            # open a web browser and show results
            webbrowser.get().open(
                f"https://google.com/search?q={quote(search_keyword.strip())}")
            return f"Here's what i found on the web for \"{search_keyword.strip()}\". Opening your web browser...\n"

        return result

    def youtube(self, search_keyword=None):
        result = ""
        browser = webbrowser.get()
        if search_keyword and browser.open(f"https://www.youtube.com/results?search_query={quote(search_keyword.strip())}"):
            result = f"I found something on Youtube for \"{search_keyword}\"."
        elif browser.open("https://www.youtube.com/"):
            result = "Ok! opening YouTube website."
        return result

    def google_maps(self, location):
        result = ""
        if location:
            # open a web browser and map
            webbrowser.get().open(
                f"https://google.nl/maps/place/{quote(location.strip())}/&amp;")
            return f"Here\'s the map location of \"{location.strip()}\". Opening your browser..."

        return result

    def wikipedia_search(self, wiki_keyword, voice_data):
        result = ""
        if wiki_keyword:
            try:
                return wikipedia.summary(wiki_keyword.strip(), sentences=2)

            except wikipedia.exceptions.WikipediaException:
                if ("who" or "who's") in voice_data.lower():
                    result = f"I don't know who that is but,"
                else:
                    result = f"I don't know what that is but,"

                return f"{result} {self.google(wiki_keyword.strip())}"

        return result

    def calculator(self, voice_data):
        operator = ""
        number1 = 0
        percentage = 0
        answer = 0
        equation = ""

        # evaluate if there are square root or cube root questions, replace with single word
        evaluated_voice_data = voice_data.replace(
            "square root", "square#root").replace("cube root", "cube#root").split()

        for word in evaluated_voice_data:
            if is_match(word, ["+", "plus", "add"]):
                operator = " + "
                equation += operator
            elif is_match(word, ["-", "minus", "subtract"]):
                operator = " - "
                equation += operator
            elif is_match(word, ["x", "times", "multiply", "multiplied"]):
                operator = " * "
                equation += operator
            elif is_match(word, ["/", "divide", "divided"]):
                operator = " / "
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
            elif word.isdigit():
                # build the equation
                equation += str(w2n.word_to_num(word)).replace(" ", "")

                # store number value for special equations (percentage, square root, cube root)
                if percentage or ("x2" in equation) or ("x3" in equation):
                    number1 = word

        if percentage:
            equation = f"{percentage}*.01*{number1}".replace(",", "")
            # evaluate percentage equation
            answer = float(eval(equation))
            # create a readable equation
            equation = f"{percentage}% of {number1}"

        # no percentage computation was made,
        # just return equivalent value of percent
        if not answer and percentage:
            return f"{percentage}% is {percentage * .01}"

        if "x2" in equation:
            equation = f"{number1}**(1./2.)"
        elif "x3" in equation:
            equation = f"{number1}**(1./3.)"

        if not answer and equation:
            try:
                # evaluate the equation made
                answer = eval(equation.replace(",", ""))
            except ZeroDivisionError:
                zero_division_responses = [
                    "The answer is somwhere between infinity, negative infinity, and undefined.", f"The answer is undefined."]
                return zero_division_responses[randint(0, len(zero_division_responses)-1)]
            except Exception as ex:
                return ""

        if answer:
            with_decimal_point = float('{:.02f}'.format(answer))

            # check answer for decimal places,
            # convert to whole number if decimal point value is ".00"
            positive_float = int((str(with_decimal_point).split('.'))[1]) > 0

            format_answer = with_decimal_point if positive_float else int(
                answer)

            # bring back the readable format of square root and cube root
            equation = equation.replace(f"{number1}**(1./2.)", f"square root of {number1}").replace(
                f"{number1}**(1./3.)", f"cube root of {number1}")

            equation = [equation, "The answer"]

            return f"{equation[randint(0, len(equation) - 1)]} is {'approximately' if positive_float else ''} {format_answer}"
        else:
            return ""

    def open_application(self, voice_data):
        confirmation = ""
        try:

            if is_match(voice_data, ["explorer", "folder"]):
                subprocess.Popen("explorer", shell=False, stdin=None,
                                 stdout=None, stderr=None, close_fds=True)
                confirmation = "Ok! opening windows explorer."
            elif is_match(voice_data, ["vs code", "visual studio code"]):
                vscode = "C:\\Users\\Dave\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe --new-window"
                subprocess.Popen(vscode, shell=False, stdin=None,
                                 stdout=None, stderr=None, close_fds=True)
                confirmation = "Ok! opening Visual Studio Code"

            elif is_match(voice_data, ["youtube", "netflix", "github", "facebook", "twitter", "instagram"]):
                app_names = []
                for web_app in voice_data.lower().split(" "):
                    url = ""

                    if web_app == "youtube" and web_app in voice_data:
                        return youtube()
                    elif web_app == "netflix" and web_app in voice_data:
                        app_names.append("Netflix")
                        url = "https://www.netflix.com/ph/"
                    elif web_app == "github" and web_app in voice_data:
                        url = "https://github.com"
                        app_names.append("Github")
                    elif web_app == "facebook" and web_app in voice_data:
                        url = "https://www.facebook.com"
                        app_names.append("Facebook")
                    elif web_app == "twitter" and web_app in voice_data:
                        url = "https://twitter.com"
                        app_names.append("Twitter")
                    elif web_app == "instagram" and web_app in voice_data:
                        url = "https://www.instagram.com"
                        app_names.append("Instagram")

                    # open the webapp in web browser
                    if url:
                        webbrowser.get().open(url)
                confirmation = f"Ok! opening {' and '.join(app_names)} in your browser."
        except Exception:
            print(
                f"\n**{self.assistant_name} could not find the specified app**\n")

        return confirmation

    def find_file(self, file_name, using_explorer=True):
        response_message = ""

        if file_name:
            # find files using windows explorer
            if using_explorer:
                # open windows explorer and look for files using queries
                explorer = f'explorer /root,"search-ms:query=*{file_name}*&crumb=location:{FILE_DIR}&"'
                subprocess.Popen(explorer, shell=False, stdin=None,
                                 stdout=None, stderr=None, close_fds=True)
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
                                    print(
                                        f"{self.assistant_name}: so far, I found {found_file_count} o/f {file_count}")
                                    self.tts.speak("Searching...")

                    except KeyboardInterrupt:
                        self.tts.speak("Search interrupted...")

                    if found_file_count > 0:
                        # show the directories of files found
                        for fl in files_found:
                            print(fl.replace("'", "").replace(
                                "(Files Found)", f"Files found: {found_file_count}"))

                        print(
                            f"\n----- {found_file_count} files found -----\n")
                        response_message = f"I found {found_file_count} files. I'm showing you the directories where to see them.\n"

        return response_message

    def screen_brightness(self, voice_data):
        percentage = int([val for val in voice_data.replace(
            '%', '').split(' ') if val.isdigit()][0]) if True else 50

        # set the screen brightness (in percentage)
        wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[
            0].WmiSetBrightness(percentage, 0)

        return percentage

    def control_wifi(self, voice_data):
        command = ""
        if "on" in voice_data:
            command = "enabled"
        elif "off" in voice_data:
            command = "disabled"

        if command:
            os.system(f"netsh interface set interface \"Wi-Fi\" {command}")

            return f"Done! I {command} the wi-fi."
        return ""

    def control_system(self, voice_data):
        command = ""
        confirmation = "no"
        if "shutdown" in voice_data:
            # shudown command sequence
            command = "shutdown /s /t 1"

        elif "restart" in voice_data:
            # restart command sequence
            command = "shutdown /r /t 1"

        if command:
            confirmation = self.tts.listen_to_audio(
                f"\033[1;33;41m Want to \"{'Restart' if '/r' in command else 'Shutdown'}\" your computer? (yes/no): ")

            # execute the shutdown/restart command if confirmed by user
            if confirmation.lower().strip() == "yes":
                os.system(command)
                return f"Ok! {'restarting...' if '/r' in command else 'shuting down...'}"
        return ""
