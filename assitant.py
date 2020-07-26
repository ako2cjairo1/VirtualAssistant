import os
import time
import json
from threading import Thread
from datetime import datetime as dt
from random import choice, randint
from colorama import init
import requests
from helper import displayException, is_match, get_commands, clean_voice_data, extract_metadata, execute_map
from tts import SpeechAssistant
from skills_library import SkillsLibrary

VIRTUAL_ASSISTANT_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\VirtualAssistant"
NEWS_SCRAPER_MODULE_DIR = "C:\\Users\\Dave\\DEVENV\\Python\\NewsScraper"

MASTER_GREEN_MESSAGE = "\033[1;37;42m"
MASTER_BLACK_NAME = "\033[22;30;42m"


class VirtualAssistant(SpeechAssistant):

    def __init__(self, masters_name, assistants_name, listen_timeout=3):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.listen_timeout = listen_timeout
        self.breaking_news_reported = []
        self.is_online = False

    def maximize_command_interface(self, maximize=True):
        if maximize:
            os.system(
                "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 900 400 /siz 491 336 /TOP")
        else:
            os.system(
                "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 1174 533 /siz 217 203 /NOT")

    def activate(self):
        skills = None
        # init news scraper (daemon)
        news = None

        def _awake_greetings(start_prompt=True):
            self.speak(choice(_get_commands("wakeup_responses")),
                       start_prompt=start_prompt)

        def _wake_assistant(listen_timeout=1, voice_data=""):
            if listen_timeout == 0:
                if not voice_data:
                    voice_data = self.listen_to_audio()

                if _deactivate(voice_data):
                    return False

                wakeup_command = _get_commands("wakeup")
                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    self.maximize_command_interface()
                    print(
                        f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")
                    self.sleep(False)
                    # play end speaking prompt sound effect
                    self.speak("<start prompt>", start_prompt=True)
                    print(f"{self.assistant_name}: (awaken)")
                    # _formulate_responses(clean_voice_data(voice_data, self.assistant_name))
                    _formulate_responses(voice_data)
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    self.maximize_command_interface()
                    print(
                        f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")
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
            if is_match(voice_data, _get_commands("mute")) or voice_data.replace("stop", "").replace("nevermind", "").strip() == "":

                if "nevermind" in voice_data:
                    self.speak("No problem. I won't")
                # minimize the command interface
                self.maximize_command_interface(False)
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
                if self.isSleeping():
                    print(
                        f"{MASTER_BLACK_NAME}{self.master_name}:{MASTER_GREEN_MESSAGE} {voice_data}")

                # play end prompt sound effect
                self.speak("<end prompt>", end_prompt=True)
                self.sleep(False)
                self.speak(choice(_get_commands("terminate_response")))
                _mute_assistant(f"stop {self.assistant_name}")

                print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                self.respond_to_bot("(Offline)")
                # terminate and end the virtual assistant application

                # volume up the music player, if applicable
                skills.music_volume(70)
                exit()

            else:
                return False

        def _unknown_responses():
            return choice(_get_commands("unknown_responses"))

        def _get_commands(command_name):
            return get_commands(command_name, self.assistant_name, self.master_name)

        def _formulate_responses(voice_data):
            response_message = ""
            ask_google = True
            ask_wikipedia = True
            ask_wolfram = True
            not_confirmation = True
            use_calc = True

            try:

                # respond to wake command(s) ("hey <assistant_name>")
                if _wake_assistant(voice_data=voice_data):
                    return

                if _mute_assistant(voice_data):
                    return

                # respond to deactivation commands
                if _deactivate(voice_data):
                    exit()

                # commands for greeting
                greeting_commands = _get_commands("greeting")
                if is_match(voice_data, greeting_commands):
                    meta_keyword = extract_metadata(
                        voice_data, greeting_commands)

                    # it's a greeting if no extracted metadata, or..
                    # metadata is assistant's name, or..
                    # metadata have matched with confirmation commands.
                    if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                        self.speak(choice(_get_commands("greeting_responses")))
                        return

                # commands to ask for assistant's name
                if is_match(voice_data, _get_commands("ask_assistant_name")):
                    self.speak(
                        f"{choice(_get_commands('ask_assistant_name_response'))}.")
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
                    music_keyword = extract_metadata(
                        voice_data, music_commands)
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
                    new_proj_metadata = extract_metadata(
                        voice_data, create_project_commands)

                    if new_proj_metadata:
                        lang = "python"
                        proj_name = "NewProjectFolder"

                        lang_idx = new_proj_metadata.find("in")
                        if lang_idx >= 0 and len(new_proj_metadata.split()) > 1:
                            lang = new_proj_metadata[(lang_idx + 2):]

                        self.speak("Ok! Just a momement.")
                        create_proj_response = skills.initiate_new_project(
                            lang=lang, proj_name=proj_name)
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
                    file_keyword = extract_metadata(
                        voice_data, find_file_commands)
                    find_file_response = skills.find_file(file_keyword)

                    if find_file_response:
                        response_message += find_file_response
                        # we found response from find_file, don't search on google or wiki
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False

                preposition_words = _get_commands("prepositions")
                # commands for news briefing
                news_commands = _get_commands(
                    "news") + [f"news {news_preposition}" for news_preposition in preposition_words]
                if is_match(voice_data, news_commands):
                    news_response = ""

                    self.speak("I'm on it...")
                    print("\n Fetching information from news channels...\n")

                    # change the directory to location of NewsTicker Library
                    os.chdir(NEWS_SCRAPER_MODULE_DIR)
                    news.fetch_news()
                    # get back to virtual assistant directory
                    os.chdir(VIRTUAL_ASSISTANT_MODULE_DIR)

                    # get meta data to use for news headline search
                    news_meta_data = extract_metadata(
                        voice_data, news_commands + preposition_words)
                    about = f"on \"{news_meta_data}\"" if news_meta_data else ""

                    # breaking news report
                    if is_match(voice_data, ["breaking news"]):
                        # if news.check_breaking_news() and self.can_listen:
                        if news.check_breaking_news():
                            news_response = _breaking_news_report(
                                on_demand=True)
                        else:
                            news_response = "Sorry, no Breaking News available (at the moment)."

                    # latest news
                    elif news.check_latest_news():
                        source_urls = []

                        # top 3 latest news report
                        if is_match(voice_data, ["news briefing", "flash briefing", "news report", "top news", "top stories", "happening today"]):
                            news_briefing = news.cast_latest_news(
                                news_meta_data)
                            number_of_results = len(news_briefing)

                            if "happening today" in voice_data:
                                # what's happening/happend from Wolfram
                                response_from_wolfram = skills.wolfram_search(
                                    voice_data)
                                if response_from_wolfram:
                                    news_response = f"{response_from_wolfram} This day in history. \n\n"

                            if number_of_results > 0:
                                if number_of_results > 2:
                                    number_of_results = 3

                                news_response += f"Here's your flash briefing {about}.\n\n"
                                for i in range(0, number_of_results):
                                    news_response += f"{news_briefing[i]['report']}\n\n"
                                    source_urls.append(
                                        news_briefing[i]["source url"])

                        # top 1 latest news report
                        elif is_match(voice_data, ["latest", "most", "recent", "flash news", "news flash"]):
                            news_deets = news.cast_latest_news(news_meta_data)
                            if len(news_deets) > 0:
                                # get the first index (latest) on the list of news
                                top_news = news_deets[0]
                                news_response = f"Here's the latest news {about}.\n {top_news['report']}\n\n"
                                source_urls.append(top_news["source url"])

                        # random news report for today
                        else:
                            latest_news = news.cast_latest_news(news_meta_data)
                            if len(latest_news) > 0:
                                if news_meta_data:
                                    news_response = f"Here's what I found {about}.\n\n"
                                # choose random news from list of latest news today
                                random_news_today = choice(latest_news)
                                news_response += f"{random_news_today['report']}\n\n"
                                source_urls.append(
                                    random_news_today["source url"])

                        if len(source_urls) > 0:
                            # convert the list of source_urls to set to remove duplicate.
                            open_source_url_thread = Thread(
                                target=execute_map, args=("open browser", set(source_urls),))
                            open_source_url_thread.start()
                            news_response += "More details of this news in the source article. It should be in your web browser now."

                    if news_meta_data and not news_response:
                        news_response = f"I couldn't find \"{news_meta_data}\" on your News Feed. Sorry about that."

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
                    location = extract_metadata(
                        voice_data, google_maps_commands)

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
                    wiki_result = skills.wikipedia_search(
                        wiki_keyword=wiki_keyword, voice_data=voice_data)

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
                    google_keyword = extract_metadata(
                        voice_data, google_commands)

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
                        self.speak(
                            choice(_get_commands("confirmation_responses")))

                        # return immediately, it is a confirmation command,
                        # we don't need further contextual answers
                        return

                # we did not found any response
                if not response_message:
                    # set the unknown response
                    response_message = _unknown_responses()

                # if not self.isSleeping():
                # anounce all the respons(es)
                self.speak(response_message)
                return True

            except Exception:
                pass
                displayException("Error forumulating response.")

        def _check_connection():
            retry_count = 0

            while True:
                try:
                    retry_count += 1
                    response = requests.get("http://google.com", timeout=300)

                    # 200 means we got connection to web
                    if response.status_code == 200:
                        # we got a connection, end the check process and proceed to remaining function
                        self.is_online = True
                        return True
                    elif retry_count == 1:
                        print(
                            f"{self.assistant_name} Not Available.\nYou are not connected to the Internet")
                    elif retry_count >= 10:
                        retry_count = 0

                except Exception:
                    pass
                    if retry_count == 1:
                        displayException(f"{self.assistant_name} Not Available.\nYou are not connected to the Internet")
                        print("\n**Trying to connect...")
                        time.sleep(5)

                time.sleep(1)

        def _announce_time():
            time_ticker = 0
            while True:
                t = dt.now()
                hr = t.hour
                mn = t.minute
                sec = t.second

                if time_ticker == 0 and (mn == 0 and sec == 0) and self.isSleeping():
                    self.speak(f"The time now is {t.strftime('%I:%M %p')}.")
                    time_ticker += 1

                    if self.isSleeping():
                        time.sleep(1)
                        # put back to normal volume level
                        skills.music_volume(70)

                # send "Fun Holiday" notification every 10:00:30 AM
                if time_ticker == 0 and ((hr == 10) and mn == 00 and sec == 30):
                    skills.fun_holiday()

                # if time_ticker == 0 and ((mn % 1) == 0 and sec == 00):
                #     # notification here
                #     pass

                if time_ticker >= 1:
                    time_ticker = 0

                time.sleep(1)

        def _breaking_news_report(on_demand=False):
            response = ""

            try:
                if news.check_breaking_news() or on_demand:
                    new_breaking_news = False
                    breaking_news_update = news.breaking_news_update

                    news_briefing = []
                    for bn in breaking_news_update:
                        if on_demand or not any(bn["headline"].lower() in breaking_news.lower() for breaking_news in self.breaking_news_reported):
                            news_briefing.append(bn["headline"])
                            new_breaking_news = True

                    if new_breaking_news:
                        self.breaking_news_reported = []
                        self.breaking_news_reported.extend(news_briefing)

                        # announce breaking news alert
                        if on_demand:
                            response += "Here's the BREAKING NEWS...\n\n"
                        else:
                            self.speak("Breaking News Alert!")

                        source_urls = [source["source url"]
                                       for source in breaking_news_update]
                        if len(source_urls) > 0:
                            # convert the list of source_urls to set to remove duplicate.
                            open_news_url_thread = Thread(
                                target=execute_map, args=("open browser", set(source_urls),))
                            open_news_url_thread.start()

                        # cast the breaking news
                        for breaking_news in news.cast_breaking_news():
                            if on_demand:
                                response += f"{breaking_news}\n\n"
                            else:
                                self.speak(breaking_news)

                        if len(source_urls) > 0:
                            more_deets_message = "More details of this breaking news in the source article. It should open in your web browser now..."
                            if not on_demand:
                                self.speak(more_deets_message)
                            response += more_deets_message

            except Exception:
                pass
                displayException(
                    "Error while reading the breaking news report.")

            if on_demand:
                return response

        def _breaking_news_notification(timeout=60):
            timeout_counter = 0

            try:
                while True:
                    if timeout_counter == 0 or timeout_counter >= timeout:
                        if news.check_breaking_news():
                            timeout_counter = 1
                            found = False

                            for bn in news.breaking_news_update:
                                if not found:
                                    headline = bn["headline"].lower()
                                    if not any(headline in breaking_news.lower() for breaking_news in self.breaking_news_reported):
                                        found = True

                                        skills.toast_notification(
                                            "Breaking News Alert!", headline)
                                        break
                    timeout_counter += 1
                    time.sleep(1)

            except Exception:
                pass

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

            # announce breaking news notification
            # every minute (60 sec)
            breaking_news_notification = Thread(
                target=_breaking_news_notification, args=(60,))
            breaking_news_notification.setDaemon(True)
            breaking_news_notification.start()

            # play speaking prompt sound effect and say greetings
            self.speak(choice(_get_commands("start_greeting")), start_prompt=True)

            try:
                while True:
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

                    elif sleep_counter > 0 and _wake_assistant(listen_time):
                        """ Listening for WAKEUP commands
                            formulate responses, then restart the loop """
                        if self.isSleeping():
                            listen_time = 0
                            sleep_counter = 0
                            _mute_assistant(f"stop {self.assistant_name}")
                        else:
                            listen_time += 1
                            sleep_counter = 0
                        continue

                    # handles if assistant is still listening for commands.
                    elif listen_time > 0:
                        """ Virtual assitant is AWAKE
                            (1) listen for high level commands, like..
                            (2) mute and deactivate commands
                            (3) formulate responses for lower level commands """

                        if listen_time == 1:
                            print(f"{self.assistant_name}: listening...")
                            self.respond_to_bot("listening...")
                        elif listen_time == randint(2, (self.listen_timeout - 2)):
                            self.speak(
                                choice(["I'm here...", "I'm listening..."]), start_prompt=False)

                        # listen for commands
                        voice_data = self.listen_to_audio()

                        # we heard a voice_data, let's start processing
                        if voice_data and not self.isSleeping():

                            # listen for mute commands, and stop listening
                            if _mute_assistant(voice_data):
                                listen_time = 0
                                sleep_counter = 0
                                # start the loop again and wait for "wake commands"
                                continue

                            # listen for deactivation commands, and terminate virtual assistant
                            elif _deactivate(voice_data):
                                return True

                            # play end prompt sound effect
                            self.speak("<end prompt>", end_prompt=True)
                            self.maximize_command_interface()

                            # start gathering answers from sources
                            _formulate_responses(voice_data)
                            sleep_counter = 0

                            # restart the listen timeout and wait for new commands
                            listen_time = 1
                            continue

                        listen_time += 1

                    else:
                        if not self.isSleeping():
                            listen_time = 1
                            sleep_counter = 0
                            continue
                        """ Virtual assistant will sleep/mute
                        (1) play end of prompt sound effect and show "ZzzzZzz"
                        (2) get updates of commands from json """
                        sleep_counter += 1
                        if sleep_counter == 1:
                            self.sleep(True)
                            # show if assistant is sleeping (muted).
                            print(f"{self.assistant_name}: ZzzzZz")
                            self.respond_to_bot("ZzzzZz")
                            # volume up the music player, if applicable
                            skills.music_volume(70)

            except Exception:
                pass
                error_message = "Error while starting virtual assistant."
                displayException(error_message)
                self.respond_to_bot(error_message)

        # check internet connectivity every second
        # before proceeding to main()
        while not _check_connection():
            recover_message = "\n**Trying to recover from internal error..."
            print(recover_message)
            self.respond_to_bot(recover_message)
            time.sleep(5)

        if self.is_online:
            skills = SkillsLibrary(super(), self.master_name, self.assistant_name)
            # init news scraper (daemon)
            news = skills.news_scraper()

            _start_virtual_assistant()
