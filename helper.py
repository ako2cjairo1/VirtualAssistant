import json
import os
import sys
import webbrowser
import linecache
import logging
import concurrent.futures as executor

logging.basicConfig(filename="VirtualAssistant.log", filemode="w",
                    level=logging.ERROR, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def displayException(exception_title="", ex_type=logging.ERROR):
    (execution_type, message, tb) = sys.exc_info()

    f = tb.tb_frame
    lineno = tb.tb_lineno
    fname = f.f_code.co_filename.split("\\")[-1]
    linecache.checkcache(fname)
    target = linecache.getline(fname, lineno, f.f_globals)
    log_data = "{}\nFile:  {}\nTarget:  {}\nMessage: {}\nLine:    {}".format(
        exception_title, fname, target.strip(), message, lineno)

    if ex_type == logging.ERROR or ex_type == logging.CRITICAL:
        print("-" * 23, end="\n")
        print(exception_title, end="\n")
        print("-" * 23, end="\n")

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
        if os.path.isfile("commands_db.json"):
            with open("commands_db.json", "r", encoding="utf-8") as fl:
                return json.load(fl)["command_db"]
    except Exception:
        pass
        displayException("Get Commands Error.")


def get_commands(command_name, assistant_name="", master_name=""):
    commands = get_commands_from_json()
    # get values of "commands", replace the placeholder name for <assistant_name> and <boss_name>
    return [com.replace("<assistant_name>", assistant_name).replace("<boss_name>", master_name) for com in (
        ([command["commands"] for command in commands if command["name"] == command_name])[0])]


def clean_voice_data(voice_data, assistants_name):
    # clean_data = voice_data.replace(assistants_name.strip().lower(), "").strip()

    return extract_metadata(voice_data, get_commands("wakeup")).replace(assistants_name, "").strip()


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
    meta_keyword, commands = convert_to_one_word_commands(voice_data, commands)
    voice_data_list = meta_keyword.lower().split(" ")
    extracted = True

    for command in (com.lower() for com in commands):
        # remove the first occurance of command from voice data
        if command in voice_data_list:
            extracted = False
            meta_keyword = meta_keyword[(meta_keyword.find(
                command) + len(command)):].strip()

            # apply recursion until we extracted the meta_data
            return extract_metadata(meta_keyword, commands)

    if extracted:
        # set to original voice_data if no meta_keword was found
        # else, use meta_keyword and make it as one string
        return (voice_data.strip().lower() if not meta_keyword else meta_keyword.strip().lower())


def execute_map(func, *argv):
    task = ""

    if "open browser" in str(func):
        func = webbrowser.get().open_new
    elif "open system" in str(func):
        func = os.system

    with executor.ThreadPoolExecutor() as exec:
        task = [result for result in zip(*argv, exec.map(func, *argv))]

    return task
