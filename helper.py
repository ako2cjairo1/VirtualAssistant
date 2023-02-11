import json
import os
import colorama
import sys
import webbrowser
import requests
import linecache
import logging
import time
import concurrent.futures as executor
from random import choice
from settings import Configuration
import platform


config = Configuration()

logging.basicConfig(filename="VirtualAssistant.log", filemode="a", level=logging.ERROR,
                    format="%(asctime)s | %(levelname)s | %(message)s", datefmt='%m-%d-%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)
clearScreenCmd = "clear" if platform.uname().system == "Darwin" else "cls"


def Log(exception_title="", ex_type=logging.ERROR):
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
        print("\n")
        print("-" * 23)
        print(f"{config.RED} {exception_title} {config.COLOR_RESET}")
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


def is_match(voice_data, keywords):
    lowercase_keywords = [keyword.lower().strip() for keyword in keywords]
    if (any(map(lambda word: word in voice_data.lower(), lowercase_keywords))):
        return True
    return False


def get_commands_from_json():
    try:
        if os.path.isfile(config.COMMANDS_DB):
            with open(config.COMMANDS_DB, "r", encoding="utf-8") as fl:
                return json.load(fl)["command_db"]

    except Exception:
        pass
        Log("Get Commands Error.")


def get_commands(command_name, assistant_name="", master_name=""):
    commands = get_commands_from_json()
    master_aliases = [master_name, "Boss", "Sir"]
    if commands:
        # get values of "commands", replace the placeholder name for <assistant_name> and <boss_name>
        return [com.replace("<assistant_name>", assistant_name).replace("<boss_name>", choice(master_aliases)) for com in (
            ([command["commands"] for command in commands if command["name"] == command_name])[0])]
    return list()


def clean_voice_data(voice_data, assistant_name):
    return extract_metadata(voice_data, get_commands("wakeup")).replace(assistant_name.lower(), "").strip()


def is_match_and_bare(voice_data, commands, assistant_name):
    meta_data = extract_metadata(voice_data, commands)
    clean_commands = [clean_voice_data(
        command, assistant_name) for command in commands]
    return extract_metadata(meta_data, clean_commands) == ""


def convert_to_one_word_commands(voice_data, commands):
    meta_keyword = voice_data.lower()
    commands = sorted(commands, key=len, reverse=True)

    for command in (com.lower() for com in commands):
        # command contains 2 or more words
        if len(command.split(" ")) > 1 and command in meta_keyword:
            # put a hyphen in between to make it a 1 word command
            meta_keyword = voice_data.replace(
                command, command.replace(" ", "-"))

    # do the same with the commands list (put hyphen in between)
    # then, sort the commands based on their length,
    # so the longer commands will be evaluated first.
    commands = sorted([com.replace(" ", "-")
                       for com in commands], key=len, reverse=True)

    return (voice_data if not meta_keyword else meta_keyword), commands


def extract_metadata(voice_data, commands):
    extraction_success = False
    extracted = True

    voice_data = voice_data.replace("?", "").replace(",", " ").strip()
    meta_keyword, commands = convert_to_one_word_commands(voice_data, commands)
    voice_data_list = meta_keyword.lower().split(" ")

    for command in (com.lower() for com in commands):
        # remove the first occurrence of command from voice data
        if command in voice_data_list:
            extracted = False
            extraction_success = True
            meta_keyword = meta_keyword[(meta_keyword.find(
                command) + len(command)):].strip()

            # apply recursion until we extracted the meta_data
            return extract_metadata(meta_keyword, commands)

    if extracted and extraction_success:
        # set to original voice_data if no meta_keyword was found
        # else, use meta_keyword and make it as one string
        return (voice_data.strip().lower() if not meta_keyword else meta_keyword.strip().lower())

    return voice_data.strip().lower()


def execute_map(func, *argv):
    task = ""

    if "open browser" in str(func):
        func = webbrowser.get().open_new
    elif "open system" in str(func):
        func = os.system

    with executor.ThreadPoolExecutor() as exec:
        task = [result for result in zip(*argv, exec.map(func, *argv))]

    return task


def check_connection(app_name=""):
    retry_count = 0

    while True:
        try:
            os.system(clearScreenCmd)
            print("\nChecking web connection...", end="")
            retry_count += 1
            response = requests.get("http://google.com", timeout=300)

            # 200 means we got connection to web
            if response.status_code == 200:
                print(f" {app_name} is Connected!")
                time.sleep(2)
                os.system(clearScreenCmd)
                # we got a connection, end the check process and proceed to remaining function
                return True

            elif retry_count == 1:
                print("You are not connected to the Internet")

            elif retry_count >= 10:
                retry_count = 0

        except requests.ConnectionError:
            if retry_count >= 3:
                raise Exception(
                    "Connection error, maximum retries already exhausted...")
            print(" Reconnecting...", end="")
            Log("Internet Connection Error. You are not connected to the Internet.")
            time.sleep(3)
            continue
        except requests.Timeout:
            if retry_count >= 3:
                raise Exception(
                    "Timeout Error, maximum retries already exhausted...")
            print(" Reconnecting...", end="")
            Log("Internet Connection Timeout Error.")
            time.sleep(3)
            continue
        except requests.RequestException:
            if retry_count >= 3:
                raise Exception(
                    "General Error, maximum retries already exhausted...")
            print(" Reconnecting...", end="")
            Log("General Connection Error")
            time.sleep(3)
            continue

        except Exception:
            raise Exception(
                "Exception occurred while checking for internet connection.")
