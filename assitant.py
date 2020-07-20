import os
import time
import requests
import json
import concurrent.futures as task
from datetime import datetime as dt
from random import choice, randint
from colorama import init
from tts import SpeechAssistant
from helper import *
from skills_library import SkillsLibrary
from threading import Thread

MASTER_GREEN_MESSAGE = "\033[1;37;42m"
MASTER_BLACK_NAME = "\033[22;30;42m"

class VirtualAssistant(SpeechAssistant):
    def __init__(self, masters_name, assistants_name, listen_timeout=3):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.listen_timeout = listen_timeout
        self.can_listen = True
        self.breaking_news_reported = []
        self.command_db = []
        self.get_commands_from_json()

    def get_commands_from_json(self):
        try:
            if os.path.isfile("commands_db.json"):
                with open("commands_db.json", "r", encoding="utf-8") as fl:
                    self.command_db = json.load(fl)["command_db"]
        except Exception:
            displayException(__name__, logging.ERROR)

    def activate(self):
        skills = SkillsLibrary(super(), self.master_name, self.assistant_name)
        
        # init news scraper (daemon)
        news = skills.news_scraper()

        def _awake_greetings(start_prompt=True):
            self.speak(choice(_get_commands("wakeup_responses")), start_prompt=start_prompt)

        def _wake_assistant(listen_timeout=1, voice_data=""):

            if listen_timeout == 0:
                if not voice_data:
                    voice_data = self.listen_to_audio()

                if _deactivate(voice_data):
                    return False

                wakeup_command = _get_commands("wakeup")
                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    print(f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")
                    self.sleep(False)
                    # play end speaking prompt sound effect
                    self.speak("<start prompt>", start_prompt=True)
                    print(f"{self.assistant_name}: (awaken)")
                    _formulate_responses(clean_voice_data(voice_data, self.assistant_name))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    print(f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")
                    print(f"{self.assistant_name}: (awaken)")
                    self.sleep(False)
                    # announce greeting from assistant
                    _awake_greetings()

                    # listen for commands
                    voice_data = self.listen_to_audio()

                    if voice_data:
                        # play end prompt sound effect before
                        self.speak("<end prompt>", end_prompt=True)
                        _formulate_responses(voice_data)
                    return True

            return False

        def _mute_assistant(voice_data):
            # commands to interrupt virtual assistant
            if is_match(voice_data, _get_commands("mute")) or voice_data.replace("stop","").strip() == "":
                
                # don't listen for commands temporarily
                print(f"{self.assistant_name}: (in mute)")
                
                # play end prompt sound effect
                self.speak("(mute/sleep prompt)", mute_prompt=True)

                self.sleep(True)
                # volume up the music player, if applicable
                skills.music_volume(70)
                return True

            return False

        def _deactivate(voice_data):
            # commands to terminate virtual assistant
            if is_match(voice_data, _get_commands("terminate")):
                if self.isSleeping:
                    print(f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")

                # play end prompt sound effect
                self.speak("<end prompt>", end_prompt=True)
                self.sleep(False)
                self.speak(choice(_get_commands("terminate_response")))
                _mute_assistant(f"stop {self.assistant_name}")

                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                # terminate and end the virtual assistant application

                # volume up the music player, if applicable
                skills.music_volume(70)
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
            ask_google = True
            ask_wikipedia = True
            ask_wolfram = True
            not_confirmation = True
            use_calc = True

            # respond to wake command(s) ("hey <assistant_name>")
            if _wake_assistant(voice_data=voice_data):
                return

            if _mute_assistant(voice_data):
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
                    return

            # commands to ask for assistant's name
            if is_match(voice_data, _get_commands("ask_assistant_name")):
                self.speak(f"{choice(_get_commands('ask_assistant_name_response'))}.")
                return

            # commands to change wallpaper
            if is_match(voice_data, _get_commands("wallpaper")):
                wallpaper_response = skills.wallpaper()

                if wallpaper_response:
                    self.speak(wallpaper_response)
                    return

            """ 
                Remove the assistant's name in voice_data
                from this point forward of code block
                to avoid misleading data.
            """
            voice_data = clean_voice_data(voice_data, self.assistant_name)

            # respond to calling assistant's name
            if voice_data == "":
                _awake_greetings(start_prompt=False)
                return

            # commands for playing music
            music_commands = _get_commands("play_music")
            if is_match(voice_data, music_commands):
                music_keyword = extract_metadata(voice_data, music_commands)
                music_response = skills.play_music(music_keyword)

                if music_response:
                    response_message += music_response
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False
                    if "Ok!" in music_response:
                        # mute assistant when playing music
                        self.sleep(True)

            # commands for controlling screen brightness, wi-fi and to shutdown/restart system
            if is_match(voice_data, (_get_commands("brightness") + _get_commands("wifi") + _get_commands("system_shutdown_restart"))):
                system_responses = ""
                if "brightness" in voice_data:
                    system_responses = skills.screen_brightness(voice_data)
                elif "wi-fi" in voice_data:
                    system_responses = skills.control_wifi(voice_data)
                elif ("shutdown" in voice_data) or ("restart" in voice_data) or ("reboot" in voice_data):
                    # if we got response from shutdown command, initiate deactivation
                    restart_msg = skills.control_system(voice_data)

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
                new_proj_metadata = extract_metadata(voice_data, create_project_commands)

                if new_proj_metadata:
                    lang = "python"
                    proj_name = "NewProjectFolder"

                    lang_idx = new_proj_metadata.find("in")
                    if lang_idx >= 0 and len(new_proj_metadata.split()) > 1:
                        lang = new_proj_metadata[(lang_idx + 2):]

                    self.speak("Ok! Just a momement.")
                    create_proj_response = skills.initiate_new_project(lang=lang, proj_name=proj_name)
                    self.speak(f"Initiating new {lang} project.")
                    self.speak(create_proj_response)
                    return

            # commands to ask time
            if is_match(voice_data, _get_commands("time")):
                response_time = skills.ask_time(voice_data)

                if response_time:
                    response_message += response_time
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

            # commands for simple math calculations
            if use_calc and is_match(voice_data, _get_commands("math_calculation")):
                calc_response = skills.calculator(voice_data)

                if calc_response:
                    response_message += calc_response
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

            # commands to open apps
            if is_match(voice_data, _get_commands("open_apps")):
                open_app_response = skills.open_application(voice_data)

                if open_app_response:
                    response_message += open_app_response
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

            # commands to find local files and document
            find_file_commands = _get_commands("find_file")
            if is_match(voice_data, find_file_commands):
                file_keyword = extract_metadata(voice_data, find_file_commands)
                find_file_response = skills.find_file(file_keyword)

                if find_file_response:
                    response_message += find_file_response
                    # we found response from find_file, don't search on google or wiki
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

            # commands for news briefing
            if is_match(voice_data, _get_commands("news")):
                news.fetch_news()
                news_response = ""

                if is_match(voice_data, ["breaking news"]):
                    if news.check_breaking_news():
                        news_response = "Here's the BREAKING NEWS...\n"
                        breaking_news_list = news.cast_breaking_news()

                        for breaking_news in breaking_news_list:
                            news_response += f"{breaking_news}\n\n"
                        
                        source_urls = [source["source url"] for source in news.breaking_news_update]
                        if len(source_urls) > 0 and len(breaking_news_list) > 0:
                            open_browser_thread = Thread(target=execute_map, args=("open browser", source_urls,))
                            open_browser_thread.start()

                            news_response += "More details of this breaking news in the source article. It should open on your web browser now..."
                            
                    else:
                        news_response = "Sorry, no BREAKING NEWS available on your news channels (at the moment)."

                elif news.check_latest_news():
                    if is_match(voice_data, ["latest", "most", "recent", "flash news", "news flash"]):
                        news_response = f"Here's the latest news...\n {news.cast_latest_news()[0]}"
                    elif is_match(voice_data, ["news briefing", "flash briefing", "news report", "top news", "top stories"]):
                        news_response = "Here's your news briefing...\n\n"
                        news_briefing = news.cast_latest_news()
                        for i in range(0,3):
                            news_response += f"{news_briefing[i]}\n\n"
                    else:
                        news_response = choice(news.cast_latest_news())

                if news_response:
                    # cast the latest news
                    response_message += news_response
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

            # commands for youtube
            youtube_commands = _get_commands("youtube")
            if is_match(voice_data, youtube_commands):
                # extract youtube keyword to search
                youtube_keyword = extract_metadata(
                    voice_data, youtube_commands)
                # search the keyword in youtube website
                youtube_response = skills.youtube(youtube_keyword)

                # we got response from youtube, now append it to list of response_message
                if youtube_response:
                    response_message += youtube_response
                    # don't search into google we found answer from youtube
                    ask_wolfram = False
                    ask_wikipedia = False
                    ask_google = False
                    not_confirmation = False
        
            # commands to use google maps
            google_maps_commands = _get_commands("google_maps")
            if ask_google and is_match(voice_data, google_maps_commands):
                # extract the location name
                location = extract_metadata(voice_data, google_maps_commands)

                if location:
                    response_message += skills.google_maps(location)
                    # don't search on google we found answers from maps
                    ask_wolfram = False
                    ask_wikipedia = False
                    ask_google = False
                    not_confirmation = False

            # commands for confirmation
            confirmation_commands = _get_commands("confirmation")

            # try wolfram for answers
            if ask_wolfram and not any(word for word in voice_data.split() if word in confirmation_commands):
                # using commands from google to extract useful meta data for wolfram search
                wolfram_response = skills.wolfram_search(voice_data)
                if wolfram_response:
                    response_message += wolfram_response
                    ask_wikipedia = False
                    ask_google = False
                    not_confirmation = False

            # commands for wikipedia, exception is "weather" commands
            wiki_commands = _get_commands("wikipedia")
            if ask_wikipedia and is_match(voice_data, wiki_commands) and not ("weather" in voice_data):
                # extract the keyword
                wiki_keyword = extract_metadata(voice_data, wiki_commands)
                # get aswers from wikipedia
                wiki_result = skills.wikipedia_search(wiki_keyword=wiki_keyword, voice_data=voice_data)

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
                    ask_google = False
                    not_confirmation = False

            # commands to search on google
            google_commands = _get_commands("google")
            if ask_google and is_match(voice_data, google_commands):
                # remove these commands on keyword to search on google
                google_keyword = extract_metadata(voice_data, google_commands)

                # search on google if we have a keyword
                if google_keyword:
                    response_message += skills.google(google_keyword)
                    not_confirmation = False

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
            return True

        def _check_connection():
            retry_count = 0

            while True:
                try:
                    retry_count += 1
                    response = requests.get("http://google.com", timeout=300)

                    # 200 means we got connection to web
                    if response.status_code == 200:
                        # we got a connection, end the check process and proceed to remaining function
                        return True
                    elif retry_count == 1:
                        print(f"{self.assistant_name} Not Available.\nYou are not connected to the Internet")
                    elif retry_count >= 10:
                        retry_count = 0

                except Exception:
                    if retry_count == 1:
                        displayException(f"{self.assistant_name} Not Available.\nYou are not connected to the Internet", logging.CRITICAL)
                        print("\n**Trying to connect...")

                time.sleep(1)

        def _announce_time():
            time_ticker = 0
            while True:
                t = dt.now()
                mn = t.minute
                sec = t.second

                if time_ticker == 0 and (mn == 0 and sec == 0):
                    self.speak(f"The time now is {t.strftime('%I:%M %p')}.")
                    time_ticker += 1

                    if self.isSleeping():
                        time.sleep(3)
                        # put back to normal volume level
                        skills.music_volume(70)

                if time_ticker >= 1:
                    time_ticker = 0

                time.sleep(1)

        def _breaking_news_report():
            time.sleep(60)

            if news.check_breaking_news():
                self.can_listen = False
                newBreakingNews = False
                news_update = news.breaking_news_update

                news_briefing = []
                for bn in news_update:
                    if not is_match(bn["headline"], self.breaking_news_reported):
                        news_briefing.append(bn["headline"])
                        newBreakingNews = True

                if newBreakingNews:
                    self.breaking_news_reported = []
                    self.breaking_news_reported.extend(news_briefing)

                    # announce breaking news alert
                    self.speak("Breaking News Alert!")
                                        
                    source_urls = [source["source url"] for source in news_update]
                    if len(source_urls) > 0:
                        open_browser_thread = Thread(target=execute_map, args=("open browser", source_urls,))
                        open_browser_thread.setDaemon(True)
                        open_browser_thread.start()

                    # cast the breaking news
                    for breaking_news in news.cast_breaking_news():
                        self.speak(breaking_news)

                    if len(source_urls) > 0:
                        self.speak("More details of this breaking news in the source article. It should open on your web browser now...")
                
                self.can_listen = True

        """
        Main handler of virtual assistant
        """

        def _start_virtual_assistant():
            # autoreset color coding of texts to normal
            init(autoreset=True)
            sleep_counter = 0
            listen_time = 1
            announce_time = True
            # volume up the music player, if applicable
            skills.music_volume(30)

            print(f"\n\n\"{self.assistant_name}\" is active...")

            announcetime_thread = Thread(target=_announce_time)
            announcetime_thread.setDaemon(True)
            announcetime_thread.start()

            check_breaking_news_thread = Thread(target=_breaking_news_report)
            check_breaking_news_thread.setDaemon(True)
            check_breaking_news_thread.start()

            # play speaking prompt sound effect and say greetings
            self.speak(choice(_get_commands("start_greeting")), start_prompt=True)
            
            try:
                while True:
                    voice_data = ""

                    # handles restarting of listen timeout
                    if listen_time >= self.listen_timeout:
                        listen_time = 0
                        # play end prompt sound effect
                        _mute_assistant(f"stop {self.assistant_name}")

                    elif self.isSleeping() and listen_time > 0:
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
                    elif listen_time > 0:
                        """ Virtual assitant is AWAKE
                            (1) listen for high level commands, like..
                            (2) greeting, mute and deactivate commands
                            (3) formulate responses for lower level commands """
                            
                        if listen_time == 1:
                            print(f"{self.assistant_name}: listening...")
                        elif listen_time == randint(2, (self.listen_timeout - 2)):
                            self.speak(choice(["I'm here...", "I'm listening..."]), start_prompt=False)

                        # listen for commands
                        if self.can_listen:
                            voice_data = self.listen_to_audio()

                        # we heard a voice_data, let's start processing
                        if voice_data:

                            # listen for mute commands, and stop listening
                            if _mute_assistant(voice_data):
                                listen_time = 0
                                sleep_counter = 0
                                # start the loop again and wait for "wake commands"
                                continue

                            # listen for deactivation commands, and end the program
                            elif _deactivate(voice_data):
                                break

                            # play end prompt sound effect
                            self.speak("<end prompt>", end_prompt=True)

                            # start gathering answers from sources
                            _formulate_responses(voice_data)
                            sleep_counter = 0

                            # restart the listen timeout and wait for new commands
                            listen_time = 1
                            continue

                        listen_time += 1

                    elif self.can_listen:
                        """ Virtual assistant will sleep/mute
                        (1) play end of prompt sound effect and show "ZzzzZzz"
                        (2) get updates of commands from json """

                        sleep_counter += 1
                        if sleep_counter == 1:
                            self.sleep(True)
                            # show if assistant is sleeping (muted).
                            print(f"{self.assistant_name}: ZzzzZz")
                            # volume up the music player, if applicable
                            skills.music_volume(70)

                            # get updates of commands from json file
                            get_commands_thread = Thread(target=self.get_commands_from_json)
                            get_commands_thread.setDaemon(True)
                            get_commands_thread.start()
            
            except:
                displayException("Error while starting virtual assistant.", logging.ERROR)

        # check internet connectivity every second
        # before proceeding to main()
        if _check_connection():
            while not _start_virtual_assistant():
                print("\n**Trying to recover from internal error...")
                time.sleep(5)
