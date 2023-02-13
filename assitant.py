import os
import subprocess
import sys
import time
import logging
from threading import Event, Thread
from datetime import datetime as dt
from random import choice, randint
from colorama import init
import requests
from helper import is_match, is_match_and_bare, get_commands, clean_voice_data, extract_metadata, execute_map, check_connection
from tts import SpeechAssistant
from skills_library import SkillsLibrary
import platform


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
        self.is_darwin_platform = True if platform.uname().system == "Darwin" else False
        self.threads = set()
        self.show_logs = False
        self.started = False

    def print(self, message):
        if not f"{self.master_name}:".lower() in message.lower():
            self.respond_to_bot(message)
        print(message)

    def maximize_command_interface(self, maximize=True):
        if not self.is_darwin_platform:
            if maximize:
                os.system(
                    "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 973 600 /siz 491 336 /TOP")
            else:
                os.system(
                    "CMDOW @ /ren \"Virtual Assistant - Brenda\" /MOV 1250 733 /siz 217 203 /NOT")

    def restart(self):
        os.system("clear" if self.is_darwin_platform else "cls")
        self.speak("Commencing restart...")
        time.sleep(2)

        print("\nCleaning up...")
        # kill daemon threads
        self.bot.kill_telegram_events()
        self.kill_tts_events()
        for thread in self.threads:
            thread.set()

        # reset global flags
        self.restart_request = False
        self.started = False

        # make sure we're in the correct directory of batch file to execute
        os.chdir(self.ASSISTANT_DIR)
        AUDIO_FOLDER = "./text-to-speech-audio"

        for aud_file in os.listdir(AUDIO_FOLDER):
            if "prompt.mp3" not in aud_file:
                audio_file = f"{AUDIO_FOLDER}/{aud_file}"
                # delete the audio file after announcing to save mem space
                os.remove(audio_file)

        os.system("clear" if self.is_darwin_platform else "cls")
        print("\nCleaning up...Done!")
        print("Updating libraries...")
        os.system('pip3 -q install -r Requirements.txt')

        os.system("clear" if self.is_darwin_platform else "cls")
        print("\nCleaning up...Done!")
        print("Updating libraries...Done!")

        os.system("clear" if self.is_darwin_platform else "cls")
        print(f"\nInitiating {self.assistant_name}...")
        # execute batch file that will open a new instance of virtual assistant
        os.system("python main.py")
        exit()

    def deactivate(self, voice_data=""):
        # commands to terminate virtual assistant
        if is_match(voice_data, self._get_commands("terminate")) or self.restart_request:

            # play end prompt sound effect
            self.speak("<end prompt>", end_prompt=True)
            self.sleep(False)

            if self.restart_request or "restart" in voice_data:
                return self.restart()
            else:
                self.restart_request = False
                self.speak(choice(self._get_commands("terminate_response")))
                self.mute_assistant(f"stop {self.assistant_name}")
                self.print(f"\n({self.assistant_name} is offline)\n")
                # volume up the music player, if applicable
                self.skills.music_volume(80)
                # terminate and end the virtual assistant application
                exit()
                sys.exit()

    def mute_assistant(self, voice_data):
        mute_commands = self._get_commands("mute")

        # commands to interrupt virtual assistant
        if is_match(voice_data, mute_commands) or is_match_and_bare(voice_data, mute_commands, self.assistant_name):

            if "nevermind" in voice_data:
                self.speak("No problem. I won't")
            # minimize the command interface
            # self.maximize_command_interface(False)

            # play end prompt sound effect
            self.speak("(mute/sleep prompt)", mute_prompt=True)

            # don't listen for commands temporarily
            self.print(f"(muted) {self.assistant_name}: ZzzzZz")
            self.sleep(True)
            # volume up the music player, if applicable
            self.skills.music_volume(80)
            return True

        return False

    def night_mode(self):
        master_aliases = [self.master_name, "Boss", "Sir"]
        self.speak(f"good night, {choice(master_aliases)}!")

        # lower the system volume
        self.skills.system_volume("20")
        # lower the screen brightness
        # self.skills.screen_brightness("15%")

        if dt.now().hour >= 18:
            music_response = self.skills.play_music(
                choice(["Vocal Jazz, Pop"]))
            if music_response:
                self.toggle_notification(False)
                self.print("Now playing relaxing music...")
                # mute and sleep assistant when playing music
                self.sleep(True)

    def day_mode(self):
        # lower the system volume
        self.skills.system_volume("55")
        # lower the screen brightness
        # self.skills.screen_brightness("70%")

        master_aliases = [self.master_name, "Boss", "Sir"]
        self.speak(f"Good morning, {choice(master_aliases)}!")

        if 2 < dt.now().hour <= 10:
            music_response = self.skills.play_music(
                choice(["post malone", "bazzi"]))
            if music_response:
                # notification is on
                self.toggle_notification(True)
                # mute and sleep assistant when playing music
                self.sleep(True)

    def toggle_notification(self, value):
        self.notification = value
        self.print(" (Notification is On)") if value else self.print(
            " (Notification is Off)")

    def _get_commands(self, command_name):
        return get_commands(command_name, self.assistant_name, self.master_name)

    def activate(self):
        def _awake_greetings(start_prompt=True):
            self.speak(choice(self._get_commands("wakeup_responses")),
                       start_prompt=start_prompt)

        def _wake_assistant(listen_timeout=1, voice_data=""):
            if listen_timeout == 0:
                if not voice_data:
                    voice_data = self.listen()

                if self.deactivate(voice_data):
                    return True

                wakeup_command = self._get_commands("wakeup")
                # wake command is invoked and the user ask question immediately.
                if len(voice_data.split(" ")) > 2 and is_match(voice_data, wakeup_command):
                    # self.maximize_command_interface()
                    self.speak("<start prompt>", start_prompt=True)
                    self.print(f"{self.assistant_name}: (awaken)")
                    self.print(
                        f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_data}")

                    self.sleep(False)
                    _formulate_responses(clean_voice_data(
                        voice_data, self.assistant_name))
                    return True

                # wake commands is invoked and expected to ask for another command
                elif is_match(voice_data, wakeup_command):
                    # self.maximize_command_interface()
                    self.print(f"{self.assistant_name}: (awaken)")
                    # self.print(
                    #     f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_data}")

                    self.sleep(False)
                    # announce greeting from assistant
                    _awake_greetings()

                    # listen for commands
                    voice_data = self.listen()

                    if voice_data:
                        # play end prompt sound effect before
                        self.speak("<end prompt>", end_prompt=True)
                        _formulate_responses(voice_data)
                    return True

            return False

        def _formulate_responses(voice_data):
            response_message = ""
            ask_google = True
            ask_wikipedia = True
            ask_wolfram = True
            not_confirmation = True
            ask_gpt = False
            adjust_system_volume = False
            isPrompt = len(voice_data) <= 35

            try:
                # if self.restart_request:
                #     return
                # respond to wake command(s) ("hey <assistant_name>")
                if _wake_assistant(voice_data=voice_data):
                    return

                if self.mute_assistant(voice_data):
                    return

                # respond to deactivation commands
                if self.deactivate(voice_data):
                    return

                # night mode
                if isPrompt and is_match(voice_data, self._get_commands("night mode")):
                    self.night_mode()
                    return

                # day mode
                if isPrompt and is_match(voice_data, self._get_commands("day mode")):
                    self.day_mode()
                    return

                # commands for greeting
                greeting_commands = self._get_commands("greeting")
                if isPrompt and is_match(voice_data, greeting_commands):
                    meta_keyword = extract_metadata(
                        voice_data, greeting_commands)

                    # it's a greeting if no extracted metadata, or..
                    # metadata is assistant's name, or..
                    # metadata have matched with confirmation commands.
                    if (not meta_keyword) or (meta_keyword == f"{self.assistant_name}".lower()):
                        self.speak(
                            choice(self._get_commands("greeting_responses")))
                        return

                # commands to ask for assistant's name
                if isPrompt and is_match(voice_data, self._get_commands("ask_assistant_name")):
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
                if isPrompt and is_match(voice_data, ["happening today", "what did I miss"]):
                    _happening_today()
                    return True

                # commands for playing music
                music_commands = self._get_commands("play_music")
                music_control_commands = self._get_commands("control_music")
                if isPrompt and is_match(voice_data, music_commands + music_control_commands):

                    if is_match(voice_data, music_control_commands) and not is_match(voice_data, music_commands):
                        setting_response = self.skills.music_setting(
                            voice_data)
                        if setting_response:
                            self.speak(setting_response)
                            self.sleep(True)
                            return True

                    music_keyword = extract_metadata(
                        voice_data, music_commands)
                    music_response = self.skills.play_music(music_keyword)

                    if music_response:
                        response_message += music_response
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False
                        if "I couldn't find" not in music_response:
                            # mute and sleep assistant when playing music
                            self.sleep(True)

                # commands for controlling screen brightness, wi-fi and to shutdown/restart system
                if isPrompt and is_match(voice_data, (self._get_commands("brightness") + self._get_commands("wifi") + self._get_commands("system_shutdown_restart"))):
                    system_responses = ""
                    if "brightness" in voice_data:
                        system_responses = self.skills.screen_brightness(
                            voice_data)
                    elif "wi-fi" in voice_data:
                        system_responses = self.skills.control_wifi(voice_data)
                    elif ("shutdown" in voice_data) or ("restart" in voice_data) or ("reboot" in voice_data):
                        # if we got response from shutdown command, initiate deactivation
                        restart_msg = self.skills.control_system(voice_data)

                        if restart_msg:
                            self.speak(restart_msg)
                            if "Ok!" in restart_msg:
                                # terminate virtual assistant
                                self.deactivate(
                                    self._get_commands("terminate")[0])
                        # return immediately, don't process for other commands any further
                        return

                    if system_responses:
                        response_message += system_responses

                # commands for controlling system volume
                system_volume_commands = self._get_commands("system volume")
                if is_match(voice_data, system_volume_commands):
                    volume_meta = extract_metadata(
                        voice_data, system_volume_commands)

                    vol_value = [value.replace("%", "") for value in volume_meta.split(
                        " ") if value.replace("%", "").isdigit()]
                    if len(vol_value):
                        vol_value = vol_value[0]
                    else:
                        vol_value = ""

                    vol = ""
                    if vol_value and is_match(voice_data, ["increase", "turn up", "up"]):
                        vol = f"-{vol_value}"
                    elif vol_value and is_match(voice_data, ["decrease", "turn down", "down"]):
                        vol = f"+{vol_value}"
                    elif isPrompt and is_match(voice_data, ["increase", "turn up", "up"]):
                        vol = "-1"
                    elif isPrompt and is_match(voice_data, ["decrease", "turn down", "down"]):
                        vol = "+1"
                    elif vol_value:
                        vol = vol_value

                    self.skills.system_volume(vol)
                    response_message += choice(
                        self._get_commands("acknowledge response"))
                    adjust_system_volume = True
                    ask_google = False
                    ask_wikipedia = False
                    ask_wolfram = False
                    not_confirmation = False

                # commands for creating a new project automation
                create_project_commands = self._get_commands("create_project")
                if isPrompt and is_match(voice_data, create_project_commands):
                    new_proj_metadata = extract_metadata(
                        voice_data, create_project_commands)

                    if new_proj_metadata:
                        lang = "python"
                        proj_name = "NewProjectFolder"

                        lang_idx = new_proj_metadata.find("in")
                        if lang_idx >= 0 and len(new_proj_metadata.split()) > 1:
                            lang = new_proj_metadata[(lang_idx + 2):]

                        alternate_responses = self._get_commands(
                            "acknowledge response")
                        self.speak(
                            f"{choice(alternate_responses)} Just a movement.")

                        create_proj_response = self.skills.initiate_new_project(
                            lang=lang, proj_name=proj_name)
                        self.speak(f"Initiating new {lang} project.")
                        self.speak(create_proj_response)
                        return

                # commands to ask time
                if isPrompt and is_match(voice_data, self._get_commands("time")):
                    response_time = self.skills.ask_time(voice_data)

                    if response_time:
                        response_message += response_time
                        ask_gpt = False
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False

                # commands to open apps
                if isPrompt and is_match(voice_data, self._get_commands("open_apps")):
                    open_app_response = self.skills.open_application(
                        voice_data)

                    if open_app_response:
                        response_message += open_app_response
                        ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False

                # commands to find local files and document
                find_file_commands = self._get_commands("find_file")
                if isPrompt and is_match(voice_data, find_file_commands):
                    file_keyword = extract_metadata(
                        voice_data, find_file_commands)
                    find_file_response = self.skills.find_file(file_keyword)

                    if find_file_response:
                        response_message += find_file_response
                        # we found response from find_file, don't search on google or wiki
                        # ask_google = False
                        ask_wikipedia = False
                        ask_wolfram = False
                        not_confirmation = False

                preposition_words = self._get_commands("prepositions")
                # commands for news briefing
                news_commands = self._get_commands(
                    "news") + [f"news {news_preposition}" for news_preposition in preposition_words]
                if isPrompt and is_match(voice_data, news_commands):
                    news_found = False

                    self.speak("I'm on it...")
                    self.print(
                        "\nFetching information from news channels...\n")

                    # get news information from sources
                    self.news.fetch_news()

                    # get meta data to use for news headline search
                    news_meta_data = extract_metadata(
                        voice_data, (news_commands + preposition_words))
                    about = f" about \"{news_meta_data}\"" if news_meta_data else ""

                    # breaking news report
                    if isPrompt and is_match(voice_data, ["breaking news"]):
                        # if news.is_new_breaking_news() and self.can_listen:
                        news_response = _breaking_news_report(on_demand=True)
                        if len(news_response) <= 0:
                            self.speak(
                                f"Sorry, no Breaking News available (at the moment).")
                            return True
                        else:
                            self.speak(news_response)
                            news_found = True

                    # latest news
                    elif self.news.check_latest_news():
                        # top 3 latest news report
                        if isPrompt and is_match(voice_data, ["news feed", "news briefing", "flash briefing", "news report", "top news", "top stories", "happening today"]):
                            news_briefing = self.news.cast_latest_news(
                                news_meta_data)
                            number_of_results = len(news_briefing)
                            if number_of_results > 2:
                                number_of_results = 3

                            news_found = True
                            self.speak(
                                f"Here are your latest news briefing{about}.")
                            for i in range(0, number_of_results):
                                news_item = news_briefing[i]
                                report = news_item["report"]
                                url = news_item["source url"]
                                is_bn = news_item["breaking_news"]

                                # let's get the redirected url (if possible) from link we have
                                redirect_url = requests.get(url)

                                # open the source article in webbrowser.
                                Thread(target=execute_map, args=(
                                    "open browser", [redirect_url.url],), daemon=True).start()

                                # tagged as breaking news
                                if is_bn == "true":
                                    self.breaking_news_reported.append(
                                        news_item["headline"])
                                    report = f"This is a Breaking News!!\n{report}"

                                # send the link to bot
                                self.speak(
                                    f"{report}\n{redirect_url.url}")

                        # # top 1 latest news report
                        elif isPrompt and is_match(voice_data, ["latest", "most", "recent", "flash news", "news flash"]):
                            news_deets = self.news.cast_latest_news(
                                news_meta_data)
                            if len(news_deets) > 0:
                                news_found = True
                                # get the first index (latest) on the list of news
                                top_news = news_deets[0]

                                report = top_news["report"]
                                # tagged as breaking news
                                if top_news["breaking_news"] == "true":
                                    self.breaking_news_reported.append(
                                        top_news["headline"])
                                    report = f"This is a Breaking News!! {about}\n\n{report}"

                                # let's get the redirected url (if possible) from link we have
                                redirect_url = requests.get(
                                    top_news["source url"])
                                # open the source article in webbrowser.
                                Thread(target=execute_map, args=(
                                    "open browser", [redirect_url.url],), daemon=True).start()
                                # send the link to bot
                                self.speak(
                                    f"{report}\n{redirect_url.url}")

                        # random news report for today
                        else:
                            latest_news = self.news.cast_latest_news(
                                news_meta_data)
                            if len(latest_news) > 0:
                                if news_meta_data:
                                    self.speak(f"Here's what I found{about}.")

                                news_found = True
                                # choose random news from list of latest news today
                                random_news_today = choice(latest_news)
                                report = random_news_today["report"]
                                url = random_news_today["source url"]
                                is_bn = random_news_today["breaking_news"]

                                # let's get the redirected url (if possible) from link we have
                                redirect_url = requests.get(url)
                                # open the source article in webbrowser.
                                Thread(target=execute_map, args=(
                                    "open browser", [redirect_url.url],), daemon=True).start()

                                report = f"{report}\n{redirect_url}"
                                # tagged as breaking news
                                if is_bn == "true":
                                    self.breaking_news_reported.append(
                                        random_news_today["headline"])
                                    report = f"This is a Breaking News!!\n{report}"

                                # send the link to bot
                                self.speak(report)

                        if news_found:
                            self.speak(
                                "More details of this news in the source article. Check on your web browser.")

                    if news_meta_data and not news_found:
                        self.speak(
                            f"I couldn't find \"{news_meta_data}\" on your News Feed. Sorry about that. \n{response_message}")

                    return True

                # commands for youtube
                youtube_commands = self._get_commands("youtube")
                if isPrompt and is_match(voice_data, youtube_commands):
                    # extract youtube keyword to search
                    google_keyword = extract_metadata(
                        voice_data, youtube_commands)
                    # search the keyword in youtube website
                    google_response = self.skills.youtube(google_keyword)

                    # we got response from youtube, now append it to list of response_message
                    if google_response:
                        response_message += google_response
                        # don't search into google we found answer from youtube
                        ask_wolfram = False
                        ask_wikipedia = False
                        # ask_google = False
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
                if ask_wolfram and isPrompt and not any(word for word in voice_data.split() if word in confirmation_commands):
                    # using commands from google to extract useful meta data for wolfram search
                    wolfram_response = self.skills.wolfram_search(voice_data)

                    # fun holiday information from timeanddate.com
                    title, message, did_you_know = self.skills.fun_holiday()
                    if wolfram_response and message and "today is" in wolfram_response:
                        wolfram_response += f"\n\nAccording to TimeAndDate.com, {message}\n{did_you_know}"
                        # what happened today in history from Wolfram|Alpha
                        today_in_history = self.skills.wolfram_search(
                            "this day in history")
                        if today_in_history:
                            wolfram_response += f"\n\nAlso, from this day in history.\n{today_in_history}"

                    if wolfram_response:
                        if 'weather' in voice_data:
                            ask_gpt = False
                        response_message += f"{wolfram_response}"
                        ask_wikipedia = False
                        ask_google = False
                        not_confirmation = False

                # commands for wikipedia, exception is "weather" commands
                wiki_commands = self._get_commands("wikipedia")
                if ask_wikipedia and isPrompt and is_match(voice_data, wiki_commands):
                    # extract the keyword
                    wiki_keyword = extract_metadata(voice_data, wiki_commands)
                    # get sawers from wikipedia
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
                        response_message += f"\nfrom Wikipedia. {wiki_result}"
                        # don't search into google we found answer from wikipedia
                        ask_google = False
                        not_confirmation = False

                # commands for youtube
                google_commands = self._get_commands("google")
                if ask_google and (isPrompt or 'stock price' in voice_data) and is_match(voice_data, google_commands):
                    # extract youtube keyword to search
                    google_keyword = extract_metadata(
                        voice_data, google_commands)
                    # search the keyword in youtube website
                    google_response = self.skills.google(google_keyword)

                    # we got response from youtube, now append it to list of response_message
                    if google_response:
                        response_message += f"{google_response}\n"
                        # don't search into google we found answer from google
                        if 'stock price' in voice_data:
                            ask_gpt = False
                        not_confirmation = False
                        ask_google = True

                if not_confirmation and len(voice_data) <= 10 and is_match(voice_data, confirmation_commands):
                    confirmation_keyword = extract_metadata(
                        voice_data, confirmation_commands).strip()

                    # it's' a confirmation if no extracted metadata or..
                    # metadata have matched with confirmation commands.
                    if not confirmation_keyword or is_match(confirmation_keyword, confirmation_commands):
                        self.speak(
                            choice(self._get_commands("confirmation_responses")))
                        # mute and sleep assistant when playing music
                        self.sleep(True)
                        # return immediately, it is a confirmation command,
                        # we don't need further contextual answers
                        return

                if not response_message or ask_gpt and not ask_google:
                    response_message += f"{self.skills.openai(voice_data)}"

                # we did not found any response
                if not response_message:
                    # set the unknown response
                    response_message = choice(
                        self._get_commands("unknown_responses"))

                # announce all the response(s).
                self.speak(response_message)

                # mute/sleep assistant if volume is adjusted
                if adjust_system_volume:
                    self.sleep(True)

                return True

            except Exception:
                pass
                self.Log("Error formulating response.")
                self.respond_to_bot("Error formulating response.")

        def _happening_today():
            # get updates from news channels
            self.news.fetch_news()

            # Today's date and time
            date_today_response_from_wolfram = self.skills.wolfram_search(
                "what day is it?")
            response_time = self.skills.ask_time("what time is it?")
            if date_today_response_from_wolfram and response_time:
                self.speak(
                    f"{date_today_response_from_wolfram} {response_time}")

            # what's weather forecast today from Wolfram|Alpha
            weather_response_from_wolfram = self.skills.wolfram_search(
                "what's the weather like?")
            # sunrise/sunset forecast today from Wolfram|Alpha
            sunrise_response_from_wolfram = self.skills.wolfram_search(
                "when is the sunrise?").split("(")[0]
            sunset_response_from_wolfram = self.skills.wolfram_search(
                "when is the sunset?").split("(")[0]
            if sunrise_response_from_wolfram and sunset_response_from_wolfram:
                self.speak(
                    f"{weather_response_from_wolfram}. \n{sunrise_response_from_wolfram} and {sunset_response_from_wolfram}")

            self.speak("Here's what's happening today.")
            # breaking news, if there's any
            breaking_news_response = _breaking_news_report(on_demand=False)
            if breaking_news_response:
                self.speak(breaking_news_response.replace("Here's the ", ""))
            else:
                # top latest news today
                news_briefing = self.news.cast_latest_news()
                number_of_results = len(news_briefing)
                if number_of_results > 0:
                    if number_of_results > 2:
                        number_of_results = 3

                    # self.speak(f"Here are the latest news today:")
                    for i in range(0, number_of_results):
                        # let's get the redirected url (if possible) from link we have
                        redirect_url = requests.get(
                            news_briefing[i]["source url"])
                        # open the source article in webbrowser.
                        Thread(target=execute_map, args=(
                            "open browser", [redirect_url.url],), daemon=True).start()
                        # send the link to bot
                        self.respond_to_bot(redirect_url.url)
                        self.speak(f"{news_briefing[i]['report']}")

            # what happened today in history from Wolfram|Alpha
            response_from_wolfram = self.skills.wolfram_search(
                "this day in history")
            if response_from_wolfram:
                self.speak("From this day in history.")
                self.speak(response_from_wolfram)

            # fun holiday information from timeanddate.com
            title, fun_holiday_info, did_you_know = self.skills.fun_holiday()
            if fun_holiday_info:
                self.speak(
                    f"From TimeandDate.com, {title}\n{fun_holiday_info}\n{did_you_know}")

            if dt.now().hour <= 10:
                music_response = self.skills.play_music(
                    choice(["post malone", "bazzi"]))
                if music_response:
                    self.speak("Now playing your morning music...")
                    # mute and sleep assistant when playing music
                    self.sleep(True)

        def _heart_beat():
            event = Event()
            start_time = dt.now()
            time_ticker = 0
            ping_count = 0
            self.threads.add(event)

            while not event.is_set():
                current_time = dt.now()
                hr = current_time.hour
                mn = current_time.minute
                sec = current_time.second

                    
                # announce the hourly time
                if time_ticker == 0 and (mn == 0 and sec == 0) and self.isSleeping() and self.notification:
                    self.speak(
                        f"The time now is {current_time.strftime('%I:%M')}.")
                    time_ticker += 1

                    if self.isSleeping():
                        time.sleep(1)
                        # put back to normal volume level
                        self.skills.music_volume(80)

                # send "Fun Holiday" notification every 10:00:30 AM
                if self.notification and time_ticker == 0 and ((hr == 10) and mn == 00 and sec == 30):
                    title, message, fun_fact = self.skills.fun_holiday()

                    if title and message and fun_fact:
                        title = f"⚠️ {title}"
                        body = f"{message}\n\n👍 {fun_fact}"
                        if self.is_darwin_platform:
                            self.skills.toast_notification(title,body)

                if ping_count >= 10:
                    ping_count = 0
                    if self.show_logs:
                        print(
                            f"{self.assistant_name}(bot) online? {self.bot.refresh_poll()}")
                    else:
                        self.bot.refresh_poll()

                    # restart if application didn't get to start
                    if not self.started:
                        self.restart_request = True
                        print(f"{self.assistant_name} didn't get to start..")

                ping_count += 1

                # Enable/Disable Notifications
                if self.bot_command:
                    # get the baseline time when to request for a restart for Telegram bot re-authentication
                    start_time = dt.now()

                    if "--disable" in self.bot_command:
                        if "notif" in self.bot_command:
                            self.toggle_notification(False)
                            self.bot.last_command = None
                        elif "log" in self.bot_command:
                            self.show_logs = False
                        self.bot.last_command = ""

                    elif "--enable" in self.bot_command:
                        if "notif" in self.bot_command:
                            self.toggle_notification(True)
                            self.bot.last_command = None
                        elif "log" in self.bot_command:
                            self.show_logs = True
                        self.bot.last_command = ""

                    if self.show_logs:
                        print(
                            f"BOT COMMAND [{current_time.strftime('%I:%M:%S')}]: {self.bot_command}")

                if not self.bot.bot_isAlive:
                    print(f"{self.assistant_name}(bot) was offline!")
                    self.kill_tts_events()
                    self.init_bot()

                # Restart request
                if self.restart_request:
                    self.deactivate("restart")
                    break

                if time_ticker >= 1:
                    time_ticker = 0

                time.sleep(1)

        def is_within_an_hour_ago(bn_time):
            return False if "hours ago)." in bn_time else True

        def _breaking_news_report(on_demand=False):
            response = ""
            source_urls = []

            try:
                # if on_demand:
                new_breaking_news = False
                news_briefing = []
                news = self.news.cast_breaking_news(on_demand)
                if on_demand and len(news) > 0:
                    news = [news[0]]

                #     if new_breaking_news or on_demand:
                max_news = 0
                # cast the breaking news
                for bn in news:
                    # report only top3 breaking news
                    if max_news >= 3:
                        break

                    headline = bn["headline"]
                    # check if headline is already reported
                    if on_demand or (is_within_an_hour_ago(bn["report"]) and (headline.lower() not in [breaking_news.lower() for breaking_news in self.breaking_news_reported])):
                        max_news += 1

                        if max_news == 1:
                            response += "Here's the BREAKING NEWS ‼️\n\n"

                        response += f"{bn['report']}\n\n"
                        news_briefing.append(headline)
                        source_urls.append(bn["source url"])

                # set as reported
                if len(news_briefing) > 0:
                    self.breaking_news_reported.extend(news_briefing)

                if len(source_urls) > 0:
                    # convert the list of source_urls to set to remove duplicate.
                    Thread(target=execute_map, args=(
                        "open browser", set(source_urls),), daemon=True).start()

            except Exception:
                pass
                self.Log("Error while reading the breaking news report.")

            return response

        def _breaking_news_notification(timeout):
            event = Event()
            timeout_counter = 0
            self.threads.add(event)

            try:
                while not event.is_set():
                    if self.restart_request:
                        # event.set()
                        break
                    elif self.isSleeping() and self.notification and (timeout_counter == 0 or timeout_counter >= int(timeout)):
                        self.news.fetch_news()
                        timeout_counter = 0
                        max_news = 0
                        news_briefing = []
                        for bn in self.news.cast_breaking_news(True):
                            if max_news < 3:
                                headline = bn["headline"]

                                # check if headline is already reported
                                if is_within_an_hour_ago(bn["report"]) and (headline.lower() not in [breaking_news.lower() for breaking_news in self.breaking_news_reported]):
                                    max_news += 1

                                    if max_news == 1:
                                        if self.is_darwin_platform:
                                            os.system(f"say 'Breaking News Alert!!'")
                                        else:
                                            self.speak("Breaking News Alert!!")

                                    self.skills.toast_notification(
                                        "‼️ * * * BREAKING NEWS * * * ‼️", bn["report"])
                                    news_briefing.append(headline)

                        # set the breaking news as "reported"
                        if len(news_briefing) > 0:
                            self.breaking_news_reported.extend(
                                news_briefing)

                    timeout_counter += 1
                    time.sleep(1)

            except Exception:
                event.set()
                self.Log("Error while sending Breaking News notification.")
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
            # self.skills.music_volume(50)
            os.system("clear" if self.is_darwin_platform else "cls")

            if self.restart_request:
                return False

            self.print(f"\n\n\"{self.assistant_name}\" is now online!\n")

            Thread(target=_heart_beat, daemon=True).start()

            # announce breaking news notification
            # every minute (60 sec)
            Thread(target=_breaking_news_notification,
                   args=(self.BREAKING_NEWS_TIMEOUT,), daemon=True).start()

            # play speaking prompt sound effect and say greetings
            self.speak(choice(self._get_commands(
                "start_greeting")), start_prompt=True)

            try:
                while True:
                    self.started = True

                    if self.restart_request:
                        break
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
                        """ Virtual assistant is AWAKE
                            (1) listen for high level commands, like..
                            (2) mute and deactivate commands
                            (3) formulate responses for lower level commands """

                        if listen_time == 1:
                            self.print(f"{self.assistant_name}: listening...")
                        elif listen_time == randint(2, (self.listen_timeout - 2)):
                            self.speak(
                                choice(["I'm here...", "I'm listening..."]), start_prompt=False)

                        # listen for commands
                        voice_data = self.listen()

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
                                return exit()

                            # play end prompt sound effect
                            self.speak("<end prompt>", end_prompt=True)
                            # self.maximize_command_interface()

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
                            # self.print(f"{self.assistant_name}: ZzzzZz")
                            # volume up the music player, if applicable
                            # self.skills.music_volume(80)

            except Exception as ex:
                self.Log(
                    f"General Error while running virtual assistant. ")
                # set the restart flag to true
                raise (ex)

        try:
            # check internet connectivity every second
            # before proceeding to starting virtual assistant
            if check_connection(self.assistant_name):
                self.skills = SkillsLibrary(
                    super(), self.master_name, self.assistant_name)
                # init news scraper (daemon)
                self.news = self.skills.news_scraper()

                _start_virtual_assistant()

        except Exception as ex:
            self.Log("Error while starting virtual assistant.")
            # time.sleep(5)
            self.skill.music_volume(50)
            # set the restart flag to true
            self.restart()
            # terminate virtual assistant
            # self.deactivate(self._get_commands("terminate")[0])
