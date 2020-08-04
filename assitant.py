import os
import sys
import time
import json
import linecache
import logging
from threading import Thread
from datetime import datetime as dt
from random import choice, randint
from colorama import init
import requests
from helper import is_match, is_match_and_bare, get_commands, clean_voice_data, extract_metadata, execute_map, check_connection
from tts import SpeechAssistant
from skills_library import SkillsLibrary

logging.basicConfig(filename="VirtualAssistant.log", filemode="a", level=logging.ERROR, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt='%m-%d-%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


def displayException(exception_title="", ex_type=logging.ERROR):
    (execution_type, message, tb) = sys.exc_info()

    f = tb.tb_frame
    lineno = tb.tb_lineno
    fname = f.f_code.co_filename.split("\\")[-1]
    linecache.checkcache(fname)
    target = linecache.getline(fname, lineno, f.f_globals)

    line_len = len(str(message)) + 10
    log_data = f"{exception_title}\n{'File:'.ljust(9)}{fname}\n{'Target:'.ljust(9)}{target.strip()}\n{'Message:'.ljust(9)}{message}\n{'Line:'.ljust(9)}{lineno}\n"
    log_data += ("-" * line_len)

    if ex_type == logging.ERROR or ex_type == logging.CRITICAL:
        print("-" * 23)
        print(exception_title)
        print("-" * 23)

    if ex_type == logging.DEBUG:
        logger.debug(log_data)

    elif ex_type == logging.INFO:
        logger.info(log_data)

    elif ex_type == logging.WARNING:
        logger.warning(log_data)

    elif ex_type == logging.ERROR:
        logger.error(log_data)

    elif ex_type == logging.CRITICAL:
        logger.critical(log_data)


class VirtualAssistant(SpeechAssistant):

    def __init__(self, masters_name, assistants_name, listen_timeout=3):
        super().__init__(masters_name, assistants_name)
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.listen_timeout = listen_timeout
        self.breaking_news_reported = []
        self.is_online = False
        self.notification = True

        self.skills = None
        # init news scraper (daemon)
        self.news = None

    def print(self, message):
        print(message)
        self.respond_to_bot(message)

    def maximize_command_interface(self, maximize=True):
        if maximize:
            os.system(
                "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 900 400 /siz 491 336 /TOP")
        else:
            os.system(
                "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 1174 533 /siz 217 203 /NOT")

    def restart(self):
        self.print("\n Comencing restart...")
        time.sleep(3)
        # make sure we're in the correct directory of batch file to execute
        os.chdir(self.ASSISTANT_DIR)
        AUDIO_FOLDER = "./text-to-speech-audio"

        self.print(" Cleaning up...")
        for aud_file in os.listdir(AUDIO_FOLDER):
            if "prompt.mp3" not in aud_file:
                audio_file = f"{AUDIO_FOLDER}/{aud_file}"
                # delete the audio file after announcing to save mem space
                os.remove(audio_file)

        self.print(" Initiating new instance...")
        # execute batch file that will open a new instance of virtual assistant
        os.system(f'start cmd /k "start_brenda.bat"')

        self.print(" Done!")
        time.sleep(3)
        sys.exit()
        exit()

    def deactivate(self, voice_data):
        # commands to terminate virtual assistant
        if is_match(voice_data, self._get_commands("terminate")):
            if self.isSleeping():
                self.print(
                    f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_data}")

            # play end prompt sound effect
            self.speak("<end prompt>", end_prompt=True)
            self.sleep(False)

            if "restart" in voice_data or self.restart_request:
                self.restart()
                self.restart_request = False

            else:
                self.speak(choice(self._get_commands("terminate_response")))
                self.mute_assistant(f"stop {self.assistant_name}")
                self.print(f"\n{self.assistant_name} assistant DEACTIVATED.\n")
                # volume up the music player, if applicable
                self.skills.music_volume(70)

            time.sleep(2)
            # terminate and end the virtual assistant application
            sys.exit()
            exit()

    def mute_assistant(self, voice_data):
        mute_commands = self._get_commands("mute")

        # commands to interrupt virtual assistant
        if is_match(voice_data, mute_commands) or is_match_and_bare(voice_data, mute_commands, self.assistant_name):

            if "nevermind" in voice_data:
                self.speak("No problem. I won't")
            # minimize the command interface
            self.maximize_command_interface(False)
            # don't listen for commands temporarily
            self.print(f"{self.assistant_name}: (in mute)")

            # play end prompt sound effect
            self.speak("(mute/sleep prompt)", mute_prompt=True)

            self.sleep(True)
            # volume up the music player, if applicable
            self.skills.music_volume(70)
            return True

        return False

    def _get_commands(self, command_name):
        return get_commands(command_name, self.assistant_name, self.master_name)

    def activate(self):
        def _awake_greetings(start_prompt=True):
            self.speak(choice(self._get_commands("wakeup_responses")),
                       start_prompt=start_prompt)

        def _wake_assistant(listen_timeout=1, voice_data=""):
            if listen_timeout == 0:
                if not voice_data:
                    voice_data = self.listen_to_audio()

                if self.deactivate(voice_data):
                    return False

                wakeup_command = self._get_commands("wakeup")
                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    self.maximize_command_interface()
                    self.print(f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_data}")
                    self.sleep(False)
                    # play end speaking prompt sound effect
                    self.speak("<start prompt>", start_prompt=True)
                    self.print(f"{self.assistant_name}: (awaken)")
                    _formulate_responses(clean_voice_data(voice_data, self.assistant_name))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    self.maximize_command_interface()
                    self.print(
                        f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_data}")
                    self.print(f"{self.assistant_name}: (awaken)")
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

        def _unknown_responses():
            return choice(self._get_commands("unknown_responses"))

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

                if self.mute_assistant(voice_data):
                    return

                # respond to deactivation commands
                if self.deactivate(voice_data):
                    sys.exit()

                # commands for greeting
                greeting_commands = self._get_commands("greeting")
                if is_match(voice_data, greeting_commands):
                    meta_keyword = extract_metadata(
                        voice_data, greeting_commands)

                    # it's a greeting if no extracted metadata, or..
                    # metadata is assistant's name, or..
                    # metadata have matched with confirmation commands.
                    if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                        self.speak(choice(self._get_commands("greeting_responses")))
                        return

                # commands to ask for assistant's name
                if is_match(voice_data, self._get_commands("ask_assistant_name")):
                    self.speak(
                        f"{choice(self._get_commands('ask_assistant_name_response'))}.")
                    return

                # commands to change wallpaper
                if is_match(voice_data, self._get_commands("wallpaper")):
                    wallpaper_response = self.skills.wallpaper()

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

                # today's breafing
                if is_match(voice_data, ["happening today", "what did I miss"]):
                    _happening_today()
                    return True

                # commands for playing music
                music_commands = self._get_commands("play_music")
                if is_match(voice_data, music_commands):
                    music_keyword = extract_metadata(
                        voice_data, music_commands)
                    music_response = self.skills.play_music(music_keyword)

                    if music_response:
                        response_message += music_response
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False
                        if "I couldn't find" not in music_response:
                            # mute and sleep assistant when playing music
                            self.sleep(True)

                # commands for controlling screen brightness, wi-fi and to shutdown/restart system
                if is_match(voice_data, (self._get_commands("brightness") + self._get_commands("wifi") + self._get_commands("system_shutdown_restart"))):
                    system_responses = ""
                    if "brightness" in voice_data:
                        system_responses = self.skills.screen_brightness(voice_data)
                    elif "wi-fi" in voice_data:
                        system_responses = self.skills.control_wifi(voice_data)
                    elif ("shutdown" in voice_data) or ("restart" in voice_data) or ("reboot" in voice_data):
                        # if we got response from shutdown command, initiate deactivation
                        restart_msg = self.skills.control_system(voice_data)

                        if restart_msg:
                            self.speak(restart_msg)
                            if "Ok!" in restart_msg:
                                # terminate virtual assistant
                                self.deactivate(self._get_commands("terminate")[0])
                        # return immediately, don't process for other commands any further
                        return

                    if system_responses:
                        response_message += system_responses
                        use_calc = False

                # commands for controlling system volume
                system_volume_commands = self._get_commands("system volume")
                if is_match(voice_data, system_volume_commands):
                    volume_meta = extract_metadata(voice_data, system_volume_commands)

                    vol_value = [value.replace("%", "") for value in volume_meta.split(" ") if value.replace("%", "").isdigit()]
                    if len(vol_value):
                        vol_value = vol_value[0]
                    else:
                        vol_value = ""

                    vol = ""
                    if vol_value and is_match(voice_data, ["increase", "turn up", "up"]):
                        vol = f"-{vol_value}"
                    elif vol_value and is_match(voice_data, ["decrease", "turn down", "down"]):
                        vol = f"+{vol_value}"
                    elif is_match(voice_data, ["increase", "turn up", "up"]):
                        vol = "-1"
                    elif is_match(voice_data, ["decrease", "turn down", "down"]):
                        vol = "+1"
                    elif vol_value:
                        vol = vol_value

                    self.skills.system_volume(vol)
                    response_message += choice(self._get_commands("acknowledge response"))
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False
                    use_calc = False

                # commands for creating a new project automation
                create_project_commands = self._get_commands("create_project")
                if is_match(voice_data, create_project_commands):
                    new_proj_metadata = extract_metadata(
                        voice_data, create_project_commands)

                    if new_proj_metadata:
                        lang = "python"
                        proj_name = "NewProjectFolder"

                        lang_idx = new_proj_metadata.find("in")
                        if lang_idx >= 0 and len(new_proj_metadata.split()) > 1:
                            lang = new_proj_metadata[(lang_idx + 2):]

                        alternate_responses = self._get_commands("acknowledge response")
                        self.speak(f"{choice(alternate_responses)} Just a momement.")

                        create_proj_response = self.skills.initiate_new_project(
                            lang=lang, proj_name=proj_name)
                        self.speak(f"Initiating new {lang} project.")
                        self.speak(create_proj_response)
                        return

                # commands to ask time
                if is_match(voice_data, self._get_commands("time")):
                    response_time = self.skills.ask_time(voice_data)

                    if response_time:
                        response_message += response_time
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False

                # commands for simple math calculations
                if use_calc and is_match(voice_data, self._get_commands("math_calculation")):
                    calc_response = self.skills.calculator(voice_data)

                    if calc_response:
                        response_message += calc_response
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False

                # commands to open apps
                if is_match(voice_data, self._get_commands("open_apps")):
                    open_app_response = self.skills.open_application(voice_data)

                    if open_app_response:
                        response_message += open_app_response
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False

                # commands to find local files and document
                find_file_commands = self._get_commands("find_file")
                if is_match(voice_data, find_file_commands):
                    file_keyword = extract_metadata(
                        voice_data, find_file_commands)
                    find_file_response = self.skills.find_file(file_keyword)

                    if find_file_response:
                        response_message += find_file_response
                        # we found response from find_file, don't search on google or wiki
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        use_calc = False

                preposition_words = self._get_commands("prepositions")
                # commands for news briefing
                news_commands = self._get_commands(
                    "news") + [f"news {news_preposition}" for news_preposition in preposition_words]
                if is_match(voice_data, news_commands):
                    news_response = ""

                    self.speak("I'm on it...")
                    self.print("\n Fetching information from news channels...\n")

                    import sys
                    sys.path.append(self.NEWS_DIR)

                    # change the directory to location of NewsTicker Library
                    os.chdir(self.NEWS_DIR)
                    self.news.fetch_news()
                    # get back to virtual assistant directory
                    os.chdir(self.ASSISTANT_DIR)

                    # get meta data to use for news headline search
                    news_meta_data = extract_metadata(
                        voice_data, news_commands + preposition_words)
                    about = f"on \"{news_meta_data}\"" if news_meta_data else ""

                    # breaking news report
                    if is_match(voice_data, ["breaking news"]):
                        # if news.check_breaking_news() and self.can_listen:
                        if self.news.check_breaking_news():
                            news_response = _breaking_news_report(on_demand=True)
                        else:
                            news_response = "Sorry, no Breaking News available (at the moment)."

                    # latest news
                    elif self.news.check_latest_news():
                        source_urls = []

                        # top 3 latest news report
                        if is_match(voice_data, ["news briefing", "flash briefing", "news report", "top news", "top stories", "happening today"]):
                            news_briefing = self.news.cast_latest_news(
                                news_meta_data)
                            number_of_results = len(news_briefing)

                            if number_of_results > 0:
                                if number_of_results > 2:
                                    number_of_results = 3

                                news_response += f"\n\nHere are your latest news briefing {about}.\n\n"
                                for i in range(0, number_of_results):
                                    news_response += f"{news_briefing[i]['report']}\n\n"
                                    source_urls.append(news_briefing[i]["source url"])

                        # top 1 latest news report
                        elif is_match(voice_data, ["latest", "most", "recent", "flash news", "news flash"]):
                            news_deets = self.news.cast_latest_news(news_meta_data)
                            if len(news_deets) > 0:
                                # get the first index (latest) on the list of news
                                top_news = news_deets[0]
                                news_response = f"Here's the latest news {about}.\n {top_news['report']}\n\n"
                                source_urls.append(top_news["source url"])

                        # random news report for today
                        else:
                            latest_news = self.news.cast_latest_news(news_meta_data)
                            if len(latest_news) > 0:
                                if news_meta_data:
                                    news_response = f"Here's what I found {about}.\n\n"
                                # choose random news from list of latest news today
                                random_news_today = choice(latest_news)
                                news_response += f"{random_news_today['report']}\n\n"
                                source_urls.append(random_news_today["source url"])

                        if len(source_urls) > 0:
                            # convert the list of source_urls to set to remove duplicate.
                            open_source_url_thread = Thread(target=execute_map, args=("open browser", set(source_urls),))
                            open_source_url_thread.setDaemon(True)
                            open_source_url_thread.start()

                            for link in set(source_urls):
                                # let get the redirected url (if possible) from link we have
                                redirect_url = requests.get(link)
                                # send the link to bot
                                self.respond_to_bot(redirect_url.url)

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
                youtube_commands = self._get_commands("youtube")
                if is_match(voice_data, youtube_commands):
                    # extract youtube keyword to search
                    youtube_keyword = extract_metadata(
                        voice_data, youtube_commands)
                    # search the keyword in youtube website
                    youtube_response = self.skills.youtube(youtube_keyword)

                    # we got response from youtube, now append it to list of response_message
                    if youtube_response:
                        response_message += youtube_response
                        # don't search into google we found answer from youtube
                        ask_wolfram = False
                        ask_wikipedia = False
                        ask_google = False
                        not_confirmation = False

                # commands to use google maps
                google_maps_commands = self._get_commands("google_maps")
                if ask_google and is_match(voice_data, google_maps_commands):
                    # extract the location name
                    location = extract_metadata(
                        voice_data, google_maps_commands)

                    if location:
                        response_message += self.skills.google_maps(location)
                        # don't search on google we found answers from maps
                        ask_wolfram = False
                        ask_wikipedia = False
                        ask_google = False
                        not_confirmation = False

                # commands for confirmation
                confirmation_commands = self._get_commands("confirmation")

                # try wolfram for answers
                if ask_wolfram and not any(word for word in voice_data.split() if word in confirmation_commands):
                    # using commands from google to extract useful meta data for wolfram search
                    wolfram_response = self.skills.wolfram_search(voice_data)
                    # fun holiday information from timeanddate.com
                    title, message, did_you_know = self.skills.fun_holiday()
                    if wolfram_response and message and "today is" in message:
                        wolfram_response += f"\n\nAccording to TimeAndDate.com, {message}\n{did_you_know}"

                    if wolfram_response:
                        response_message += wolfram_response
                        ask_wikipedia = False
                        ask_google = False
                        not_confirmation = False

                # commands for wikipedia, exception is "weather" commands
                wiki_commands = self._get_commands("wikipedia")
                if ask_wikipedia and is_match(voice_data, wiki_commands):
                    # extract the keyword
                    wiki_keyword = extract_metadata(voice_data, wiki_commands)
                    # get aswers from wikipedia
                    wiki_result = self.skills.wikipedia_search(
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
                google_commands = self._get_commands("google")
                if ask_google and is_match(voice_data, google_commands):
                    # remove these commands on keyword to search on google
                    google_keyword = extract_metadata(
                        voice_data, google_commands)

                    # search on google if we have a keyword
                    if google_keyword:
                        response_message += self.skills.google(google_keyword)
                        not_confirmation = False

                if not_confirmation and is_match(voice_data, confirmation_commands):
                    confimation_keyword = extract_metadata(
                        voice_data, confirmation_commands).strip()

                    # it's' a confirmation if no extracted metadata or..
                    # metadata have matched with confirmation commands.
                    if not confimation_keyword or is_match(confimation_keyword, confirmation_commands):
                        self.speak(choice(self._get_commands("confirmation_responses")))
                        # # play end prompt sound effect and go to sleep
                        # self.mute_assistant(f"stop {self.assistant_name}")
                        # mute and sleep assistant when playing music
                        self.sleep(True)
                        # return immediately, it is a confirmation command,
                        # we don't need further contextual answers
                        return

                # we did not found any response
                if not response_message:
                    # set the unknown response
                    response_message = _unknown_responses()

                # if not self.isSleeping():
                # anounce all the respons(es) except "success" response result, those wrere already announced.
                if response_message != "success":
                    self.speak(response_message)
                return True

            except Exception:
                displayException("Error forumulating response.")
                self.respond_to_bot("Error forumulating response.")

        def _happening_today():
            # Today's date and time
            date_today_response_from_wolfram = self.skills.wolfram_search("what day is it?")
            response_time = self.skills.ask_time("what time is it?")

            # breaking news, if there's any
            breaking_news_response = _breaking_news_report(on_demand=True)

            # top latest news today
            news_briefing = self.news.cast_latest_news()
            number_of_results = len(news_briefing)

            # what happend today in history from Wolfram|Alpha
            response_from_wolfram = self.skills.wolfram_search("this day in history")

            # fun holiday information from timeanddate.com
            title, fun_holiday_info, did_you_know = self.skills.fun_holiday()

            # what's weather forecast today from Wolfram|Alpha
            weather_response_from_wolfram = self.skills.wolfram_search("what's the weather like?")

            # sunrise/sunset forecast today from Wolfram|Alpha
            sunrise_response_from_wolfram = self.skills.wolfram_search("when is the sunrise?").split("(")[0]
            sunset_response_from_wolfram = self.skills.wolfram_search("when is the sunset?").split("(")[0]

            if date_today_response_from_wolfram and response_time:
                self.speak(f"{date_today_response_from_wolfram} {response_time}")

            self.speak("Here's what's happening today.")

            if breaking_news_response:
                self.speak(breaking_news_response.replace("Here's the ", ""))

            if number_of_results > 0:
                if number_of_results > 2:
                    number_of_results = 3

                self.speak(f"Here are the latest news today:")
                for i in range(0, number_of_results):
                    # let's get the redirected url (if possible) from link we have
                    redirect_url = requests.get(news_briefing[i]["source url"])
                    # send the link to bot
                    self.respond_to_bot(redirect_url.url)
                    self.speak(f"{news_briefing[i]['report']}")

            if response_from_wolfram:
                self.speak("From this day in history.")
                self.speak(response_from_wolfram)

            if fun_holiday_info:
                self.speak(f"From timeanddate.com, {title}\n{fun_holiday_info}\n{did_you_know}")

            if weather_response_from_wolfram:
                self.speak(weather_response_from_wolfram)

            if sunrise_response_from_wolfram and sunset_response_from_wolfram:
                self.speak(f"{sunrise_response_from_wolfram} and {sunset_response_from_wolfram}")

            if dt.now().hour <= 10:
                music_response = self.skills.play_music("morning music")
                if music_response:
                    self.speak("Now playing your morning music...")
                    # mute and sleep assistant when playing music
                    self.sleep(True)

        def _heart_beat():
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
                        self.skills.music_volume(70)

                # send "Fun Holiday" notification every 10:00:30 AM
                if self.notification and time_ticker == 0 and ((hr == 10) and mn == 00 and sec == 30):
                    title, message, _ = self.skills.fun_holiday()
                    self.skills.toast_notification(title, message)

                # Enable/Disable Notifications
                if self.bot_command:
                    if "/disable notification" in self.bot_command:
                        self.notification = False
                        self.print(" (Notification is Off)")
                        self.bot.last_command = None

                    elif "/enable notification" in self.bot_command:
                        self.notification = True
                        self.print(" (Notification is On)")
                        self.bot.last_command = None

                # Restart request
                if not self.polling or self.restart_request:
                    self.bot_command = f"restart {self.assistant_name}"

                if time_ticker >= 1:
                    time_ticker = 0

                time.sleep(1)

        def _breaking_news_report(on_demand=False):
            response = ""

            try:
                if self.news.check_breaking_news() or on_demand:
                    new_breaking_news = False
                    breaking_news_update = self.news.breaking_news_update

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
                            open_news_url_thread = Thread(target=execute_map, args=("open browser", set(source_urls),))
                            open_news_url_thread.setDaemon(True)
                            open_news_url_thread.start()

                            for link in set(source_urls):
                                # let get the redirected url (if possible) from link we have
                                redirect_url = requests.get(link)
                                # send the link to bot
                                self.respond_to_bot(redirect_url.url)

                        # cast the breaking news
                        for breaking_news in self.news.cast_breaking_news():
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
                        if self.news.check_breaking_news() and self.notification:
                            timeout_counter = 1

                            news_briefing = []
                            headlines = ""
                            for bn in self.news.breaking_news_update:
                                headline = bn["headline"]
                                if not any(headline.lower() in breaking_news.lower() for breaking_news in self.breaking_news_reported):
                                    news_briefing.append(bn["headline"])
                                    headlines += f">> {headline}\n\n"

                            if len(news_briefing) > 0:
                                if len(headlines) > 255:
                                    # use the firts headline if the whole news is > 255 chars
                                    headlines = f">> {news_briefing[0]} ..more"
                                    if len(headlines) > 255:
                                        headlines = f">> {news_briefing[0][:240]}...more"

                                self.skills.toast_notification("* * * BREAKING NEWS * * *", headlines)

                    timeout_counter += 1
                    time.sleep(1)

            except Exception:
                pass
                displayException("Error while sending Breaking News notification.")

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
            self.skills.music_volume(30)

            if self.restart_request:
                return False

            self.print(f"\n\n\"{self.assistant_name}\" is active...")

            announcetime_thread = Thread(target=_heart_beat)
            announcetime_thread.setDaemon(True)
            announcetime_thread.start()

            # announce breaking news notification
            # every minute (60 sec)
            breaking_news_notification = Thread(
                target=_breaking_news_notification, args=(60,))
            breaking_news_notification.setDaemon(True)
            breaking_news_notification.start()

            time.sleep(3)
            # play speaking prompt sound effect and say greetings
            self.speak(choice(self._get_commands("start_greeting")), start_prompt=True)

            try:
                while True:
                    # handles restarting of listen timeout
                    if listen_time >= self.listen_timeout:
                        listen_time = 0
                        # play end prompt sound effect
                        self.mute_assistant(f"stop {self.assistant_name}")

                    elif self.isSleeping() and listen_time > 0:
                        # listen for mute commands, and stop listening
                        self.mute_assistant(f"stop {self.assistant_name}")
                        listen_time = 0
                        sleep_counter = 0

                    elif sleep_counter > 0 and _wake_assistant(listen_time):
                        """ Listening for WAKEUP commands
                            formulate responses, then restart the loop """
                        if self.isSleeping():
                            listen_time = 0
                            sleep_counter = 0
                            self.mute_assistant(f"stop {self.assistant_name}")
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
                            self.print(f"{self.assistant_name}: listening...")
                        elif listen_time == randint(2, (self.listen_timeout - 2)):
                            self.speak(
                                choice(["I'm here...", "I'm listening..."]), start_prompt=False)

                        # listen for commands
                        voice_data = self.listen_to_audio()

                        # we heard a voice_data, let's start processing
                        if voice_data and not self.isSleeping():

                            # listen for mute commands, and stop listening
                            if self.mute_assistant(voice_data):
                                listen_time = 0
                                sleep_counter = 0
                                # start the loop again and wait for "wake commands"
                                continue

                            # listen for deactivation commands, and terminate virtual assistant
                            elif self.deactivate(voice_data):
                                return sys.exit(0)

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
                            self.print(f"{self.assistant_name}: ZzzzZz")
                            # volume up the music player, if applicable
                            self.skills.music_volume(70)

            except Exception as ex:
                displayException(f"General Error while running virtual assistant.")

        try:
            # check internet connectivity every second
            # before proceeding to starting virtual assistant
            if check_connection():
                self.skills = SkillsLibrary(super(), self.master_name, self.assistant_name)
                # init news scraper (daemon)
                self.news = self.skills.news_scraper()

                while not _start_virtual_assistant():
                    time.sleep(5)
                    os.system("cls")
                    brenda = VirtualAssistant(masters_name=self.master_name, assistants_name=self.assistant_name, listen_timeout=self.listen_timeout)
                    brenda.maximize_command_interface()
                    brenda.activate()

        except Exception:
            displayException("Error while starting virtual assistant.")
            time.sleep(5)

            # os.system("cls")
            self.bot_command = f"restart {self.assistant_name}"
            self.skill.music_volume(20)
            # set the restart flag to true
            self.restart_request = True
            self.restart()
