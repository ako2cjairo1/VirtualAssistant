import os
import time
from assitant import VirtualAssistant
import platform


def create_instance():
    brenda = None
    os.system("clear" if platform.uname().system == "Darwin" else "cls")

    try:
        brenda = VirtualAssistant(
            masters_name="Dave", assistants_name="Alexa", listen_timeout=10)
        brenda.activate()

    except Exception as ex:
        print(f"Something went wrong when creating new instance! {ex}")
        time.sleep(2)
        os.system('pip3 install -r Requirements.txt clear;python main.py')
        time.sleep(5)
        create_instance()


if __name__ == "__main__":
    create_instance()
