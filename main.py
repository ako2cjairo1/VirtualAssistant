import os
import time
from assitant import VirtualAssistant


def create_instance():
    os.system("cls")
    brenda = None

    try:
        brenda = VirtualAssistant(masters_name="Dave", assistants_name="Alexa", listen_timeout=10)
        brenda.maximize_command_interface()
        brenda.activate()

    except Exception as ex:
        print(f"Critical Error occurred, trying to start a new instance... {str(ex)}")
        time.sleep(5)
        create_instance()


if __name__ == "__main__":
    os.system("cls")
    create_instance()
