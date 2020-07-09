import os
import time
import requests
import json
import concurrent.futures as task
from datetime import datetime as dt
from random import choice
from colorama import init
from tts import SpeechAssistant
from helper import *
from controls_library import ControlLibrary


class VirtualAssistant(SpeechAssistant):
    def __init__(self, masters_name, assistants_name, listen_timeout=3):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.listen_timeout = listen_timeout
        self.sleep_assistant = False
        self.command_db = []
        self.get_commands_from_json()

    def get_commands_from_json(self):
        if os.path.isfile("commands_db.json"):
            with open("commands_db.json", "r", encoding="utf-8") as fl:
                self.command_db = json.load(fl)["command_db"]

    def activate(self):
        control = ControlLibrary(super(), self.assistant_name)

        def _awake_greetings(start_prompt=True):
            self.speak(choice(_get_commands("wakeup_responses")),
                       start_prompt=start_prompt)

        def _wake_assistant(listen_timeout=1):
            voice_data = ""

            if listen_timeout == 0:
                voice_data = self.listen_to_audio()
                wakeup_command = _get_commands("wakeup")

                if _deactivate(voice_data):
                    return

                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    # play end speaking prompt sound effect
                    self.speak("(start prompt)", start_prompt=True)
                    submitTaskWithException(_formulate_responses, clean_voice_data(
                        voice_data, self.assistant_name))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    # announce greeting from assistant
                    _awake_greetings()

                    # listen for commands
                    voice_data = self.listen_to_audio()

                    if voice_data:
                        # play end prompt sound effect before
                        self.speak("(end prompt)", end_prompt=True)
                        submitTaskWithException(
                            _formulate_responses, voice_data)
                    return True

                # listen for deactivation commands, and end the program
                elif _deactivate(voice_data):
                    return False

            return False

        def _mute_assistant(voice_data):
            # commands to interrupt virtual assistant
            if is_match(voice_data, _get_commands("mute")):

                # don't listen for commands temporarily
                print(f"{self.assistant_name}: (muted)")
                return True

            return False

        def _deactivate(voice_data):
            # commands to terminate virtual assistant
            if is_match(voice_data, _get_commands("terminate")):
                self.speak(choice(_get_commands("terminate_response")))
                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                # terminate and end the virtual assistant application
                exit()
            else:
                return False

        def _unknown_responses():
            return choice(_get_commands("unknown_responses"))

        def _get_commands(action):
            # get values of "commands", replace the placeholder name for <assistant_name> and <boss_name>
            return [com.replace("<assistant_name>", self.assistant_name).replace("<boss_name>", self.master_name) for com in (
                ([command["commands"] for command in self.command_db if command["name"] == action])[0])]

        def _formulate_responses(voice_data):
            response_message = ""
            search_google = True
            search_wiki = True
            not_confirmation = True
            use_calc = True

            # respond to wake command(s) ("hey <assistant_name>")
            if _wake_assistant():
                # then exit immediately
                return

            # respond to deactivation commands
            if _deactivate(voice_data):
                return

            # commands for greeting
            greeting_commands = _get_commands("greeting")
            if is_match(voice_data, greeting_commands):
                meta_keyword = extract_metadata(voice_data, greeting_commands)

                # it's a greeting if no extracted metadata, or..
                # metadata is assistant's name, or..
                # metadata have matched with confirmation commands.
                if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                    self.speak(choice(_get_commands("greeting_responses")))
                    # return immediately, we don't need contextual answers
                    return

            # commands to ask for assistant's name
            if is_match(voice_data, _get_commands("ask_assistant_name")):
                self.speak(
                    f"{choice(_get_commands('ask_assistant_name_response'))}.")
                # return immediately we don't need any answers below
                return

            # commands to change wallpaper
            wallpaper_commands = _get_commands("wallpaper")
            if is_match(voice_data, wallpaper_commands):
                wallpaper_response = submitTaskWithException(control.wallpaper)

                if wallpaper_response:
                    self.speak(wallpaper_response)
                    return

            """ 
                Remove the assistant's name in voice_data
                from this point forward of code block
                to avoid misleading data.
            """
            voice_data = clean_voice_data(voice_data, self.assistant_name)

            # commands for playing music
            music_commands = _get_commands("play_music")
            if is_match(voice_data, music_commands):
                music_keyword = extract_metadata(voice_data, music_commands)
                music_response = submitTaskWithException(
                    control.play_music, music_keyword)
                if music_response:
                    response_message += music_response
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False
                    if "Ok!" in music_response:
                        # mute assistant when playing music
                        self.sleep_assistant = True

            # commands for controlling screen brightness
            brightness_commands = _get_commands("brightness")
            # commands to control wi-fi
            wifi_commands = _get_commands("wifi")
            # commands to control system
            system_shutdown_commands = _get_commands("system_shutdown_restart")
            if is_match(voice_data, (brightness_commands + wifi_commands + system_shutdown_commands)):
                system_responses = ""
                if "brightness" in voice_data:
                    system_responses = submitTaskWithException(
                        control.screen_brightness, voice_data)
                elif "wi-fi" in voice_data:
                    system_responses = submitTaskWithException(
                        control.control_wifi, voice_data)
                elif ("shutdown" in voice_data) or ("restart" in voice_data) or ("reboot" in voice_data):
                    # if we got response from shutdown command, initiate deactivation
                    restart_msg = submitTaskWithException(
                        control.control_system, voice_data)

                    if restart_msg:
                        self.speak(restart_msg)
                        if "Ok!" in restart_msg:
                            # terminate virtual assistant
                            _deactivate(_get_commands("terminate")[0])
                    # return immediately, don't process for other commands any further
                    return

                if system_responses:
                    response_message += system_responses
                    use_calc = False

            # commands for creating a new project automation
            create_project_commands = _get_commands("create_project")
            if is_match(voice_data, create_project_commands):
                new_proj_metadata = extract_metadata(
                    voice_data, create_project_commands)
                if new_proj_metadata:
                    lang = "python"
                    proj_name = "NewProjectFolder"

                    lang_idx = new_proj_metadata.find("in")
                    if lang_idx >= 0 and len(new_proj_metadata.split()) > 1:
                        lang = new_proj_metadata[(lang_idx + 2):]

                    self.speak("Ok! Just a momement.")
                    create_proj_response = submitTaskwargsWithException(
                        control.initiate_new_project, lang=lang, proj_name=proj_name)
                    self.speak(f"Initiating new {lang} project.")
                    self.speak(create_proj_response)
                    return

            # commands to ask time
            if is_match(voice_data, _get_commands("time")):
                response_time = submitTaskWithException(
                    control.ask_time, voice_data)
                if response_time:
                    response_message += response_time
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands for simple math calculations
            if use_calc and is_match(voice_data, _get_commands("math_calculation")):
                calc = submitTaskWithException(control.calculator, voice_data)
                if calc:
                    response_message += calc
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands to open apps
            if is_match(voice_data, _get_commands("open_apps")):
                open_app_response = submitTaskWithException(
                    control.open_application, voice_data)
                if open_app_response:
                    response_message += open_app_response
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands to find local files and document
            find_file_commands = _get_commands("find_file")
            if is_match(voice_data, find_file_commands):
                file_keyword = extract_metadata(voice_data, find_file_commands)
                find_file_response = submitTaskWithException(
                    control.find_file, file_keyword)

                if find_file_response:
                    response_message += find_file_response
                    # we found response from find_fil, don't search on google or wiki
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands for wikipedia, exception is "weather" commands
            wiki_commands = _get_commands("wikipedia")
            if search_wiki and is_match(voice_data, wiki_commands) and not ("weather" in voice_data):
                # extract the keyword
                wiki_keyword = extract_metadata(voice_data, wiki_commands)
                # get aswers from wikipedia
                wiki_result = submitTaskwargsWithException(
                    control.wikipedia_search, wiki_keyword=wiki_keyword, voice_data=voice_data)

                keyword_list = wiki_keyword.lower().split(" ")
                # if answer from wikipedia contains more than 2 words
                if len(keyword_list) > 2:
                    match_count = 0

                    for word in keyword_list:
                        # and matched with context of question, return wikipedia answer
                        if word in wiki_result.lower():
                            match_count += 1
                    if match_count < 4:
                        # else, return nothing
                        wiki_result = ""

                if wiki_result:
                    response_message += wiki_result
                    # don't search into google we found answer from wikipedia
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands for youtube
            youtube_commands = _get_commands("youtube")
            if is_match(voice_data, youtube_commands):
                # extract youtube keyword to search
                youtube_keyword = extract_metadata(
                    voice_data, youtube_commands)
                # search the keyword in youtube website
                youtube_response = submitTaskWithException(
                    control.youtube, youtube_keyword)

                # we got response from youtube, now append it to list of response_message
                if youtube_response:
                    response_message += youtube_response
                    # don't search into google we found answer from youtube
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands to use google maps
            google_maps_commands = _get_commands("google_maps")
            if search_google and is_match(voice_data, google_maps_commands):
                # extract the location name
                location = extract_metadata(voice_data, google_maps_commands)

                if location:
                    response_message += submitTaskWithException(
                        control.google_maps, location)
                    # don't search on google we found answers from maps
                    search_google = False
                    search_wiki = False
                    not_confirmation = False
                    use_calc = False

            # commands to search on google
            google_commands = _get_commands("google")
            if search_google and is_match(voice_data, google_commands):
                # remove these commands on keyword to search on google
                google_keyword = extract_metadata(voice_data, google_commands)

                # search on google if we have a keyword
                if google_keyword:
                    response_message += submitTaskWithException(
                        control.google, google_keyword)

            # commands for confirmation
            confirmation_commands = _get_commands("confirmation")
            if not_confirmation and is_match(voice_data, confirmation_commands):
                confimation_keyword = extract_metadata(
                    voice_data, confirmation_commands).strip()

                # it's' a confirmation if no extracted metadata or..
                # metadata have matched with confirmation commands.
                if not confimation_keyword or is_match(confimation_keyword, confirmation_commands):
                    self.speak(choice(_get_commands("confirmation_responses")))

                    # return immediately, it is a confirmation command,
                    # we don't need further contextual answers
                    return

            # we did not found any response
            if not response_message:
                # set the unknown response
                response_message = _unknown_responses()

            # anounce all the respons(es)
            self.speak(response_message)

        def _check_connection():
            while True:
                try:
                    response = requests.get("http://google.com", timeout=300)
                    # 200 means we got connection to web
                    if response.status_code == 200:
                        # we got a connection, end the check process and proceed to remaining function
                        return True

                except Exception as ex:
                    displayException(
                        "**Virtual assistant failed to initiate. No internet connection.", logging.WARNING)
                time.sleep(1)

        def _announce_time(announce_time=False):
            t = dt.now()
            mn = t.minute
            sec = t.second

            if announce_time or (mn == 0 and sec <= 4):
                self.speak(f"The time now is {t.strftime('%I:%M %p')}")
                return True
            else:
                return False

        """
        Main handler of virtual assistant
        """

        def start_virtual_assistant():
            # autoreset color coding of texts to normal
            init(autoreset=True)
            sleep_counter = 0
            listen_time = 0
            announce_time = True

            print(
                f"\n\nVirtual assistant \"{self.assistant_name}\" is active...")

            # generate random start greeting
            announce_greeting = choice(_get_commands("start_greeting"))

            while True:
                # handles restarting of listen timeout
                if listen_time >= (self.listen_timeout + 1):
                    listen_time = 0

                if self.sleep_assistant:
                    self.sleep_assistant = False
                    # listen for mute commands, and stop listening
                    _mute_assistant(f"stop {self.assistant_name}")
                    listen_time = 0
                    sleep_counter = 0

                elif _wake_assistant(listen_time):
                    """ Listening for WAKEUP commands
                        formulate responses, then restart the loop """
                    listen_time += 1
                    sleep_counter = 0
                    # continue the loop without listening to another command
                    continue

                # handles if assistant is still listening for commands.
                if announce_greeting or listen_time > 0:
                    """ Virtual assitant is AWAKE
                        (1) listen for high level commands, like..
                        (2) greeting, mute and deactivate commands
                        (3) formulate responses for lower level commands """
                    if not announce_greeting:
                        # print(f"{self.assistant_name}: listening... {listen_time} of {self.listen_timeout}")
                        if listen_time == 1:
                            print(f"{self.assistant_name}: listening...")
                    else:
                        # play begin speaking prompt sound effect
                        self.speak("(start prompt)", start_prompt=True)

                    # listen for commands
                    voice_data = self.listen_to_audio(announce_greeting)

                    # we heard a voice_data, let's start processing
                    if voice_data:
                        # listen for mute commands, and stop listening
                        if _mute_assistant(voice_data):
                            listen_time = 0
                            # start the loop again and wait for "wake commands"
                            continue
                        # listen for deactivation commands, and end the program
                        elif _deactivate(voice_data):
                            break
                        # respond to calling assistant's name
                        elif voice_data.lower() == self.assistant_name.lower():
                            _awake_greetings(start_prompt=False)
                            sleep_counter = 0
                            announce_greeting = None
                            # restart the listen timeout and wait for new commands
                            listen_time = 1
                            continue

                        # play end prompt sound effect
                        self.speak("(end prompt)", end_prompt=True)

                        # start gathering answers from sources
                        submitTaskWithException(
                            _formulate_responses, voice_data)
                        sleep_counter = 0
                        announce_greeting = None

                        # restart the listen timeout and wait for new commands
                        listen_time = 1
                        continue

                    listen_time += 1

                else:
                    """ Virtual assistant will sleep/mute
                    (1) play end of prompt sound effect and show "ZzzzZzz"
                    (2) get updates of commands from json """
                    sleep_counter += 1
                    if sleep_counter == 1:
                        # play end prompt sound effect
                        self.speak("(mute/sleep prompt)", mute_prompt=True)

                    if (sleep_counter == 1):  # or ((sleep_counter % 20) == 0):
                        # every 20th cycle, show if assistant is sleeping (muted).
                        print(f"{self.assistant_name}: ZzzzZz")

                    # get updates of commands from json file
                    self.get_commands_from_json()

                _announce_time()
                announce_greeting = None

        # check internet connectivity every second
        # before proceeding to main()
        if _check_connection():
            while not submitTaskWithException(start_virtual_assistant):
                print("\n**Trying to recover from internal error...")
                time.sleep(5)
