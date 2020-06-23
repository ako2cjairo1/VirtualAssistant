import os
import time
import requests
import json
from random import randint
from colorama import init
from tts import SpeechAssistant
from helper import clean_voice_data, extract_metadata, is_match
from controls_library import ControlLibrary


class VirtualAssistant(SpeechAssistant):
    def __init__(self, masters_name, assistants_name):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.command_db = []
        self.get_commands_from_json()

    def get_commands_from_json(self):
        if os.path.isfile("commands_db.json"):
            with open("commands_db.json", "r", encoding="utf-8") as fl:
                self.command_db = json.load(fl)["command_db"]

    def activate(self):
        control = ControlLibrary(super(), self.assistant_name)

        def awake_greetings():
            wake_responses = _get_commands("wakeup_responses")
            self.speak(wake_responses[randint(
                0, len(wake_responses) - 1)])

        def wake_assistant(listen_timeout=1):
            voice_data = ""

            if listen_timeout == 0:
                voice_data = self.listen_to_audio()
                wakeup_command = _get_commands("wakeup")

                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    formulate_responses(clean_voice_data(
                        voice_data, self.assistant_name))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    # announce greeting from assistant
                    awake_greetings()

                    # listen for commands
                    voice_data = self.listen_to_audio()

                    if voice_data:
                        formulate_responses(voice_data, self.assistant_name)
                    return True

                # listen for deactivation commands, and end the program
                elif deactivate(voice_data):
                    return False

            return False

        def mute_assistant(voice_data):
            # commands to interrupt virtual assistant
            if is_match(voice_data, _get_commands("mute")):

                # don't listen for commands temporarily
                print(f"{self.assistant_name}: (muted)")
                return True

            return False

        def deactivate(voice_data):
            # commands to terminate virtual assistant
            if is_match(voice_data, _get_commands("terminate")):
                self.speak("\nHappy to help! Goodbye!")
                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                # terminate and end the virtual assistant application
                exit()

        def unknown_responses():
            unknown_responses = _get_commands("unknown_responses")
            return unknown_responses[randint(0, len(unknown_responses) - 1)]

        def _get_commands(action):
            # get values of "commands", replace the placeholder name for <assistant_name> and <boss_name>
            return [com.replace("<assistant_name>", self.assistant_name).replace("<boss_name>", self.master_name) for com in (
                ([command["commands"] for command in self.command_db if command["name"] == action])[0])]

        def formulate_responses(voice_data):
            response_message = ""
            search_google = True
            search_wiki = True
            not_confirmation = True

            # respond to wake commands
            if wake_assistant():
                # then exit immediately
                return

            # respond to deactivation commands
            if deactivate(voice_data):
                return

            # commands for greeting
            greeting_commands = _get_commands("greeting")
            # responses to greeting
            greeting_responses = _get_commands("greeting_responses")

            if is_match(voice_data, greeting_commands):
                meta_keyword = extract_metadata(
                    voice_data, greeting_commands).lower().strip()

                print()
                # if no metakeyword or if metakeyword is equal to assistant's name,
                # then, this is just a greeting
                if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                    self.speak(greeting_responses[randint(
                        0, len(greeting_responses) - 1)])
                    # return immediately, we don't need contextual answers
                    return

            # commands to ask for assistant's name
            if is_match(voice_data, _get_commands("ask_assistant_name")):
                ask_name_response = _get_commands(
                    "ask_assistant_name_response")

                self.speak(
                    f"{ask_name_response[randint(0, len(ask_name_response) - 1)]}.")
                # return immediately we don't need any answers below
                return

            """ 
                Remove the assistant's name in voice_data
                from this point forward of code block
                to avoid misleading data.
            """
            voice_data = clean_voice_data(voice_data, self.assistant_name)

            # commands for controlling screen brightness
            brightness_commands = _get_commands("brightness")
            # commands to control wi-fi
            wifi_commands = _get_commands("wifi")
            # commands to control system
            system_shutdown_commands = _get_commands("system_shutdown_restart")

            if is_match(voice_data, (brightness_commands + wifi_commands + system_shutdown_commands)):
                system_responses = ""
                if "brightness" in voice_data:
                    brightness_percentage = control.screen_brightness(
                        voice_data)
                    if brightness_percentage:
                        system_responses = f"Ok! I set the brightness by {brightness_percentage}%"
                elif "wi-fi" in voice_data:
                    system_responses = control.control_wifi(voice_data)
                elif ("shutdown" in voice_data) or ("restart" in voice_data):
                    system_responses = control.control_system(voice_data)

                if system_responses:
                    response_message += system_responses

            # commands to ask time
            if is_match(voice_data, _get_commands("time")):
                response_time = control.ask_time(voice_data)
                if response_time:
                    response_message += response_time
                    search_google = False
                    search_wiki = False

            # commands for simple math calculations
            if is_match(voice_data, _get_commands("math_calculation")):
                calc = control.calculator(voice_data)
                if calc:
                    response_message += calc
                    search_google = False
                    search_wiki = False

            # commands to open apps
            if is_match(voice_data, _get_commands("open_apps")):
                open_app_response = control.open_application(voice_data)
                if open_app_response:
                    response_message += open_app_response
                    not_confirmation = False

            # commands to find local files and document
            find_file_commands = _get_commands("find_file")

            if is_match(voice_data, find_file_commands):
                file_keyword = extract_metadata(voice_data, find_file_commands)
                find_file_response = control.find_file(file_keyword)

                if find_file_response:
                    response_message += find_file_response
                    # we found response from find_fil, don't search on google or wiki
                    search_google = False
                    search_wiki = False

            # commands for wikipedia
            wiki_commands = _get_commands("wikipedia")
            if search_wiki and is_match(voice_data, wiki_commands):
                # extract the keyword
                wiki_keyword = extract_metadata(voice_data, wiki_commands)
                # get aswers from wikipedia
                wiki_result = control.wikipedia_search(
                    wiki_keyword, voice_data)

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

            # commands for youtube
            youtube_commands = _get_commands("youtube")

            if is_match(voice_data, youtube_commands):
                # extract youtube keyword to search
                youtube_keyword = extract_metadata(
                    voice_data, youtube_commands)
                # search the keyword in youtube website
                youtube_response = control.youtube(youtube_keyword)

                # we got response from youtube, now append it to list of response_message
                if youtube_response:
                    response_message += youtube_response
                    # don't search into google we found answer from youtube
                    search_google = False

            # commands to use google maps
            google_maps_commands = _get_commands("google_maps")

            if search_google and is_match(voice_data, google_maps_commands):
                # extract the location name
                location = extract_metadata(voice_data, google_maps_commands)

                if location:
                    response_message += control.google_maps(location)
                    # don't search on google we found answers from maps
                    search_google = False

            # commands to search on google
            google_commands = _get_commands("google")

            if search_google and is_match(voice_data, google_commands):
                # remove these commands on keyword to search on google
                google_keyword = extract_metadata(voice_data, google_commands)

                # search on google if we have a keyword
                if google_keyword:
                    response_message += control.google(google_keyword)

            # commands for confirmation
            confirmation_commands = _get_commands("confirmation")
            confirmation_responses = _get_commands("confirmation_responses")

            if not_confirmation and is_match(voice_data, confirmation_commands):
                if not extract_metadata(voice_data, confirmation_commands).strip():
                    self.speak(confirmation_responses[randint(
                        0, len(confirmation_responses) - 1)])

                    # return immediately, it is a confirmation command,
                    # we don't need further contextual answers
                    return

            # we did not found any response
            if not response_message:
                # set the unknown response
                response_message = unknown_responses()

            # anounce all the respons(es)
            self.speak(response_message)

        def check_connection():
            # check internet connectivity (every 5 seconds)
            # before proceeding to main()
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
                    print(f"**ERROR** : {ex}")
                    print(
                        "**Virtual assistant failed to initiate. No internet connection.\n")

                time.sleep(5)

        """
        Main handler of virtual assistant
        """

        def main():
            # autoreset color coding of texts to normal
            init(autoreset=True)

            sleep_counter = 0
            listen_timeout = 0

            print(
                f"\nVirtual assistant \"{self.assistant_name}\" is active...")

            start_greetings = _get_commands("start_greeting")
            # generate random start greeting
            announce_greeting = start_greetings[randint(
                0, len(start_greetings) - 1)]

            while True:
                # handles restarting of listen timeout
                if listen_timeout >= 6:
                    listen_timeout = 0

                # try to wake the assistant
                elif wake_assistant(listen_timeout):
                    listen_timeout += 1
                    sleep_counter = 0
                    # continue the loop without listening to another command
                    continue

                # handles if assistant is still listening for commands.
                if announce_greeting or listen_timeout > 0:
                    print(
                        f"{self.assistant_name}: ... (listen timeout {listen_timeout} of 5)")

                    # listen for commands
                    voice_data = self.listen_to_audio(announce_greeting)

                    # listen for mute commands, and stop listening
                    if mute_assistant(voice_data):
                        listen_timeout = 10
                        # start the loop again and wait for "wake commands"
                        continue

                    # listen for deactivation commands, and end the program
                    if deactivate(voice_data):
                        break

                    if voice_data:
                        formulate_responses(voice_data)
                        sleep_counter = 0
                        # deduct listen timeout
                        if 1 < listen_timeout <= 5:
                            listen_timeout -= 1
                            continue

                    listen_timeout += 1

                else:
                    sleep_counter += 1
                    if (sleep_counter == 1) or ((sleep_counter % 20) == 0):
                        # every 20th cycle, show if assistant is sleeping (muted).
                        print(f"{self.assistant_name}: ZzzzZz")

                    # if assistant is sleeping,
                    # get updates of commands from json file
                    self.get_commands_from_json()

                announce_greeting = None

        check_connection()
