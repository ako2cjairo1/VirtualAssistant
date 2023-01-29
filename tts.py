import re
import speech_recognition as sr
import os
import sys
import random
import playsound as sound
import colorama
import linecache
import logging
import time
from helper import is_match, is_match_and_bare, check_connection
from gtts import gTTS
from gtts.tts import gTTSError
from settings import Configuration
from skills_library import SkillsLibrary
from telegram import TelegramBot
from threading import Event, Thread
from datetime import datetime as dt

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s", "%m-%d-%Y %I:%M:%S %p")

file_handler = logging.FileHandler("VirtualAssistant.log", mode="a")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class SpeechAssistant(Configuration):

    def __init__(self, masters_name, assistants_name):
        super().__init__()
        self.master_name = masters_name
        self.assistant_name = assistants_name
        self.sleep_assistant = False
        self.not_available_counter = 0
        self.recognizer = sr.Recognizer()
        # let's override the dynamic threshold to 4000,
        # so the timeout we set in listen() will be used
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 4000

        self.skill = SkillsLibrary(self, self.master_name, self.assistant_name)
        self.speaker = None
        self.restart_request = False
        self.bot = None
        self.bot_command = None
        self.init_bot()

    def Log(self, exception_title="", ex_type=logging.ERROR):
        log_data = ""

        if ex_type == logging.ERROR or ex_type == logging.CRITICAL:
            (execution_type, message, tb) = sys.exc_info()

            f = tb.tb_frame
            lineno = tb.tb_lineno
            fname = f.f_code.co_filename.split("\\")[-1]
            linecache.checkcache(fname)
            target = linecache.getline(fname, lineno, f.f_globals)

            line_len = len(str(message)) + 10
            log_data = f"{exception_title}\n{'File:'.ljust(9)}{fname}\n{'Target:'.ljust(9)}{target.strip()}\n{'Message:'.ljust(9)}{message}\n{'Line:'.ljust(9)}{lineno}\n"
            log_data += ("-" * line_len)

        else:
            log_data = exception_title

        if ex_type == logging.ERROR or ex_type == logging.CRITICAL:
            print("-" * 23)
            print(f"{self.RED} {exception_title} {self.COLOR_RESET}")
            print("-" * 23)

        if ex_type == logging.DEBUG:
            logger.debug(log_data)

        elif ex_type == logging.INFO:
            logger.info(log_data)

        elif ex_type == logging.WARNING:
            logger.warning(log_data)

        elif ex_type == logging.ERROR:
            logger.error(log_data)
            raise Exception(exception_title)

        elif ex_type == logging.CRITICAL:
            logger.critical(log_data)
            raise Exception(exception_title)

    def listen_to_audio(self, ask=None):
        voice_text = ""
        listen_timeout = 3
        phrase_limit = 10

        if self.isSleeping():
            listen_timeout = 2
            phrase_limit = 5

        # adjust the recognizer sensitivity to ambient noise
        # and record audio from microphone
        with sr.Microphone() as source:
            if not self.isSleeping():
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                # announce/play something before listening from microphone
                if ask:
                    self.speak(ask)

                if self.bot_command and "/" not in self.bot_command:
                    voice_text = self.bot_command

                else:
                    # listening
                    audio = self.recognizer.listen(
                        source, timeout=listen_timeout, phrase_time_limit=phrase_limit)
                    # try convert audio to text/string data
                    voice_text = self.recognizer.recognize_google(audio)

                self.not_available_counter = 0

            except sr.UnknownValueError:
                self.Log(
                    f"{self.assistant_name} could not understand what you have said.", logging.WARNING)

                if self.isSleeping() and self.not_available_counter >= 3:
                    message = f"\"{self.assistant_name}\" is active again."
                    # print(message)
                    # self.respond_to_bot(message)
                    self.not_available_counter = 0

                return voice_text

            except sr.RequestError:
                self.not_available_counter += 1
                if self.not_available_counter == 3:
                    message = f"\"{self.assistant_name}\" Not Available."
                    self.Log(message)
                    # self.respond_to_bot(message)

                if self.isSleeping() and self.not_available_counter >= 3:
                    message = f"{self.assistant_name}: reconnecting..."
                    print(message)
                    self.respond_to_bot(message)

            except gTTSError:
                self.Log("Exception occurred in speech service.")

            except Exception as ex:
                if "listening timed out" not in str(ex):
                    # bypass the timed out exception, (timeout=3, if total silence for 3 secs.)
                    self.Log("Exception occurred while analyzing audio.")

        if not self.isSleeping() and voice_text.strip():
            print(f"{self.BLACK_GREEN}{self.master_name}:{self.GREEN} {voice_text}")

        if (not self.isSleeping() and not self.bot_command and voice_text.strip()):
            self.respond_to_bot(f"(I hear you say): \"{voice_text}\"")

        if voice_text.strip():
            self.bot.last_command = None

        return voice_text.strip()

    def sleep(self, value):
        self.sleep_assistant = value

    def isSleeping(self):
        return self.sleep_assistant

    def init_bot(self):
        try:
            self.bot = TelegramBot()
            self.bot_command = None

            if check_connection("Telegram bot"):
                Thread(target=self.poll_bot, daemon=True).start()
                Thread(target=self.handle_bot_commands, daemon=True).start()

        except Exception:
            self.Log("Error while initiating telegram bot.")
            time.sleep(5)
            self.restart_request = True
            self.init_bot()

    def respond_to_bot(self, audio_string):
        # don't send response to bot with audio_string containing "filler" phrases.
        if not is_match(audio_string, ["I'm here...", "I'm listening...", "(in mute)", "listening...", f"hey {self.assistant_name}"]):
            audio_string = audio_string.replace(f"{self.assistant_name}:", "")
            self.bot.send_message(audio_string)

    def poll_bot(self):
        poll_evt = Event()
        while not poll_evt.is_set():
            try:
                if self.restart_request:
                    poll_evt.set()
                self.bot.poll()

            except Exception:
                poll_evt.set()
                self.Log(
                    "Exception occurred while polling bot, trying to re-connect...")
                time.sleep(5)
                os.system("python main.py")
                self.restart_request = True
                continue

    def handle_bot_commands(self):
        poll_evt = Event()

        while not poll_evt.is_set():
            try:
                # get the latest command from bot
                self.bot_command = self.bot.last_command

                # handles the RESTART command sequence of virtual assistant application
                if self.bot_command and ("/restart" in self.bot_command):
                    self.bot_command = f"reset {self.assistant_name}"
                    # lower the volume of music player (if it's currently playing)
                    # so listening microphone will not block our bot_command request
                    self.skill.music_volume(30)
                    # set the restart flag to true
                    self.restart_request = True
                    poll_evt.set()
                    break

                elif self.bot_command:
                    # lower the volume of music player (if it's currently playing)
                    # so listening microphone will not block our bot_command request
                    self.skill.music_volume(30)
                    # let's use a wakeup command if she's sleeping.
                    if self.isSleeping():
                        self.bot_command = f"hey {self.assistant_name} {self.bot_command}"

                time.sleep(0.4)

            except Exception:
                self.Log("Error while handling bot commands.")
                self.restart_request = True
                time.sleep(5)
                continue

    def speak(self, audio_string, start_prompt=False, end_prompt=False, mute_prompt=False):
        if audio_string.strip():
            try:
                removeUrl = re.sub(r"https?:\/\/[^\s]+", "", audio_string)
                # volume up the music player, if applicable
                if not self.isSleeping():
                    self.skill.music_volume(30)
                force_delete = False
                # init google's text-to-speech module
                # tts = gTTS(text=audio_string, lang="en",
                #            tld="com", lang_check=False, slow=False)

                # make sure we're in the correct directory of batch file to execute
                os.chdir(self.ASSISTANT_DIR)

                if not os.path.isdir(self.AUDIO_FOLDER):
                    os.mkdir(self.AUDIO_FOLDER)

                # generate a filename for the audio file generated by google
                # audio_file = f"{self.AUDIO_FOLDER}/assistants-audio-{str(random.randint(1, 1000))}.mp3"

                if start_prompt and "<start prompt>" in audio_string:
                    sound.playsound(f"{self.AUDIO_FOLDER}/start prompt.mp3")

                elif start_prompt and audio_string:
                    # tts.save(audio_file)
                    self.respond_to_bot(audio_string)
                    sound.playsound(f"{self.AUDIO_FOLDER}/start prompt.mp3")
                    print(
                        f"{self.BLACK_CYAN}{self.assistant_name}:{self.CYAN} {audio_string}")
                    os.system(f"say \"{removeUrl}\"")
                    # respond to bot as well
                    force_delete = True

                elif end_prompt:
                    sound.playsound(f"{self.AUDIO_FOLDER}/end prompt.mp3")

                elif mute_prompt:
                    sound.playsound(f"{self.AUDIO_FOLDER}/mute prompt.mp3")

                elif audio_string:
                    # tts.save(audio_file)
                    self.respond_to_bot(audio_string)
                    print(
                        f"{self.BLACK_CYAN}{self.assistant_name}:{self.CYAN} {audio_string}")
                    os.system(f"say \"{removeUrl}\"")
                    # respond to bot as well

                # if not start_prompt and not end_prompt and not mute_prompt or force_delete:
                #     # delete the audio file after announcing to save mem space
                #     os.remove(audio_file)

            except Exception as ex:
                if not ("Cannot find the specified file." or "Permission denied:") in str(ex):
                    self.Log("Exception occurred while trying to speak.")
                    # message = f"\"{self.assistant_name}\" Not Available."
                    # self.respond_to_bot(message)
                    # try to invoke the speak function once again
                    self.speak(audio_string)
