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
from helper import *
from urllib.parse import quote
from random import choice
from datetime import datetime as dt
from word2number import w2n

FILE_DIR = "c:\\users\\dave"
VIRTUAL_ASSISTANT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\VirtualAssistant"
UTILITIES_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\PythonUtilityProjects"
INIT_PROJECT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\ProjectGitInitAutomation"
PSE_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\PSE"
DEV_PATH_DIR = os.environ.get("DevPath")
WOLFRAM_APP_ID = os.environ.get("WOLFRAM_APP_ID")


class ControlLibrary:
    def __init__(self, tts, masters_name, assistants_name):
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.tts = tts    
    
    def ask_time(self, voice_data):
        if "in" in voice_data.lower().split(" "):
            return ""
        else:
            time_prefix = ["It's", "The time is"]
            return f'{choice(time_prefix)} {dt.now().strftime("%I:%M %p")}'

    def google(self, search_keyword):
        # open google iste in web browser and show results
        if search_keyword and webbrowser.get().open(f"https://google.com/search?q={quote(search_keyword.strip())}"):
            return f"Here's what I found on the web for \"{search_keyword.strip()}\". Opening your web browser...\n"

        return ""

    def youtube(self, search_keyword=None):
        # open youtube site in web browser and show results
        if search_keyword and webbrowser.get().open(f"https://www.youtube.com/results?search_query={quote(search_keyword.strip())}"):
            return f"I found something on Youtube for \"{search_keyword}\"."
        return ""

    def google_maps(self, location):
        result = ""
        if location:
            # open a web browser and map
            webbrowser.get().open(
                f"https://google.nl/maps/place/{quote(location.strip())}/&amp;")
            return f"Here\'s the map location of \"{location.strip()}\". Opening your browser..."

        return result

    def wolfram_search(self, voice_data):
        client = wolframalpha.Client(WOLFRAM_APP_ID)
        res = client.query(voice_data)
        response = ""

        try:
            # get answers from Wolfram Alpha
            wolfram_response = next(res.results).text

            # if no answers found return a blank response
            no_data_responses = ["(data not available)", "(no data available)"]
            if is_match(wolfram_response, no_data_responses):
                return response

            # remove "according to" phrase in wolfram response
            if "(according to" in wolfram_response.lower():
                wolfram_response = wolfram_response.split("(according to")[0]

            # replace "Q:" and "A:" prefixes and replace new space instead
            if is_match(wolfram_response, ["Q: ", "A: "]):
                wolfram_response = wolfram_response.replace("Q: ", "").replace("A: ", "\n\n") 

            wolfram_meta = wolfram_response.split("|")
            parts_of_speech = ["noun", "pronoun", "verb", "adjective", "adverb", "preposition", "conjunction", "interjection"]
            
            if wolfram_response.count("|") > 2:
                if is_match(wolfram_response, parts_of_speech):
                    response = f"({wolfram_meta[1]}) \nIt means, {wolfram_meta[2][:(len(wolfram_meta[2]) - 2)]}."
                else:
                    response = "Here's some information."
                    print(f"\n{wolfram_response}\n")
                

            elif "|" in wolfram_response:
                if "time" in voice_data.lower():
                    if len(wolfram_response.split(":")[0]) == 2:
                        response = f"{wolfram_response[:5]} {wolfram_response[9:11]}"
                    else:
                        response = f"{wolfram_response[:4]} {wolfram_response[8:10]}"
                elif "my name is" in wolfram_response.lower():
                    response = wolfram_response[:(wolfram_response.lower().find("my name is") + 11)] + self.assistant_name + ". Are you " + self.master_name + "?"
                else:
                    
                    if is_match(wolfram_response, parts_of_speech):
                        response = f"[{wolfram_meta[0]}] \nIt means, {wolfram_meta[-1]}."
                    else:
                        response = wolfram_response

            else:
                if "how do you spell" or "spell" in voice_data:
                    response = f'{wolfram_response}. \n\n{" . ".join(list(wolfram_response.upper()))}'
                else:
                    response = wolfram_response

            return response
            
        except:
            return response

    def wikipedia_search(self, wiki_keyword, voice_data):
        result = ""
        if wiki_keyword:
            try:
                return wikipedia.summary(wiki_keyword.strip(), sentences=2)

            except wikipedia.exceptions.WikipediaException as wex:
                displayException("from Wikipedia (handled)", logging.INFO)

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
        answer = None
        equation = ""

        # evaluate if there are square root or cube root questions, replace with single word
        evaluated_voice_data = voice_data.replace(",", "").replace(
            "square root", "square#root").replace("cube root", "cube#root").split(" ")

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

        if (answer is None) and equation:
            try:
                # evaluate the equation made
                answer = eval(equation.replace(",", ""))
            except ZeroDivisionError:
                return choice(["The answer is somwhere between infinity, negative infinity, and undefined.", f"The answer is undefined."])
            except Exception:
                displayException("Calculator control_library (handled)", logging.INFO)
                return ""

        if not answer is None:
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

            return f"{choice(equation)} is {'approximately ' if positive_float else ''}{format_answer}"
        else:
            return ""

    def open_application(self, voice_data):
        confirmation = ""
        app_names = []

        def modified_app_names():
            clean_app_names = voice_data
            special_app_names = ["vs code", "ms code", "ms vc", "microsoft excel", "spread sheet", "ms excel", "microsoft word", "ms word", "microsoft powerpoint", "ms powerpoint", "task scheduler",
                                 "visual studio code", "pse ticker", "command console", "command prompt", "control panel", "task manager", "resource monitor", "resource manager", "device manager", "windows services", "remove programs", "add remove"]
            for name in special_app_names:
                if name in voice_data:
                    # make one word app name by using hyphen
                    clean_app_names = clean_app_names.replace(
                        name, name.replace(" ", "-"))

            # return unique list of words/app names
            return {word for word in clean_app_names.split(" ")}

        try:
            app_commands = []
            urls = []

            for app in modified_app_names():
                if is_match(app, ["explorer", "folder"]):
                    app_commands.append("start explorer C:\\Users\\Dave\\DEVENV\\Python")
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

                elif is_match(app, ["pse-ticker", "pse"]):
                    app_names.append("Philippine Stock Exchange Ticker")
                    # change directory to PSE library resides
                    os.chdir(PSE_MODULE_DIR)
                    # open PSE ticker in new window
                    os.system(f'start cmd /k \"start_PSE.bat\"')
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
                mapTaskWithException("open system", app_commands)

            # open the webapp in web browser
            if len(urls) > 0:
                mapTaskWithException("open browser", urls)

            if len(app_names) > 0:
                confirmation = f"Ok! opening {' and '.join(app_names)}..."

        except Exception:
            displayException(
                f"**{self.assistant_name} could not find the specified app**", logging.DEBUG)

        return confirmation

    def find_file(self, file_name, using_explorer=True):
        response_message = ""

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
                                    print(
                                        f"{self.assistant_name}: so far, I found {found_file_count} o/f {file_count}")
                                    self.tts.speak("Searching...")

                    except KeyboardInterrupt as ex:
                        displayException(f"Find File (handled)", logging.INFO)
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
        percentage = int([val for val in voice_data.replace('%', '').split(' ') if val.isdigit()][0]) if True else 50
        # set the screen brightness (in percentage)
        wmi.WMI(namespace="wmi").WmiMonitorBrightnessMethods()[0].WmiSetBrightness(percentage, 0)

        return f"Ok! I set the brightness by {percentage}%"

    def control_wifi(self, voice_data):
        command = ""
        if "on" in voice_data or "open" in voice_data:
            command = "enabled"
        elif "off" in voice_data or "close" in voice_data:
            command = "disabled"

        if command:
            # announce before going off-line
            self.tts.speak(f"Done! I {command} the wi-fi.\n")
            os.system(f"netsh interface set interface \"Wi-Fi\" {command}")
            print(f"\033[1;33;41m{self.assistant_name} is offline...")
            # although this will not be annouced anymore (offline), let's rather return something.
            return f"Done! I {command} the wi-fi."
        return ""

    def control_system(self, voice_data):
        command = ""
        confirmation = "no"
        if "shutdown" in voice_data:
            # shudown command sequence for 15 seconds
            command = "shutdown /s /t 15"

        elif is_match(voice_data, ["restart", "reboot"]):
            # restart command sequence for 15 seconds
            command = "shutdown /r /t 15"

        if command:
            confirmation = self.tts.listen_to_audio(f"\033[1;33;41m Are you sure to \"{'Restart' if '/r' in command else 'Shutdown'}\" your computer? (yes/no): ")

            # execute the shutdown/restart command if confirmed by user
            if "yes" in confirmation.lower().strip():
                os.system(command)
                return f"Ok! {'Reboot' if '/r' in command else 'Shutdown'} sequence will commence in approximately 10 seconds..."
            return f"{'Reboot' if '/r' in command else 'Shutdown'} is canceled."

        return ""

    def wallpaper(self):
        import sys
        sys.path.append(UTILITIES_MODULE_DIR)
        from wallpaper import Wallpaper

        wp = Wallpaper()
        wp.change_wallpaper()
        return "Ok! I changed your wallpaper..."

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

        import sys
        sys.path.append(UTILITIES_MODULE_DIR)
        from musicplayer import MusicPlayer
        mp = MusicPlayer()

        # change the directory to location of batch file to execute
        os.chdir(UTILITIES_MODULE_DIR)
        
        meta_data = voice_data.strip().lower().replace("&", "and").replace("music", "").replace("songs", "")


        if meta_data == "":
            # mode = "compact"
            response = f"Ok! Playing all songs{', shuffled' if shuffle == 'True' else '...'}"
            songWasFound = True
        
        elif meta_data and "by" in meta_data.split(" ") and meta_data.find("by") > 0 and len(meta_data.split()) >= 3:
            option = '"play by"'

            by_idx = meta_data.find("by")
            title = f'"{meta_data[:(by_idx - 1)].strip()}"'
            artist = f'"{meta_data[(by_idx + 3):].strip()}"'
            genre = title

            temp = mp.search_song_by(meta_data[:(by_idx - 1)].strip(), meta_data[(by_idx + 3):].strip(), meta_data[:(by_idx - 1)].strip())
            if temp:
                songWasFound = True
                response = f"Ok! Playing {title} by {artist}..."
            else:
                response = f"I couldn't find '{title}' in your music."

        
        elif meta_data:
            option = '"play by"'
            title = f'"{meta_data}"'
            artist = f'"{meta_data}"'
            genre = f'"{meta_data}"'

            mp.title = meta_data
            mp.artist = meta_data
            mp.genre = meta_data

            temp = mp.search_song_by(meta_data, meta_data, meta_data)
            if temp:
                songWasFound = True
                response = f"Ok! Now playing '{meta_data}' music..."
            else:
                response = f"I couldn't find '{meta_data}' in your music."
		
        if songWasFound:
            # batch file to play some music in new window
            os.system(f'start cmd /k "play_some_music.bat {option} {shuffle} {mode} {title} {artist} {genre}"')

        # get back to virtual assistant directory
        os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

        return response

    def control_music(self, command):
        response = ""
        wsh = comctl.Dispatch("WScript.Shell")

        command = command.strip().lower()
        if command == "stop":
            wsh.SendKeys("{F4}")
            response = "Stop music..."
        elif command == "shuffle":
            wsh.SendKeys("{F5}")
            response = "Shuffle music..."
        elif command == "shuffle":
            wsh.SendKeys("{F5}")
            response = "Unshuffled music..."
        elif command == "play":
            wsh.SendKeys("{F9}")
            response = "Playing music..."
        elif command == "pause":
            wsh.SendKeys("{F9}")
            response = "Pause music..."
        elif command == "next":
            wsh.SendKeys("{F10}")
            response = "Playing next song..."
        return response