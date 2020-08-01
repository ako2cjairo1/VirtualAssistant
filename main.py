import os
import time
from assitant import VirtualAssistant


def create_instance():
    os.system("cls")
    brenda = None

    try:
        brenda = VirtualAssistant(masters_name="Dave", assistants_name="Brenda", listen_timeout=10)
        brenda.maximize_command_interface()
        brenda.activate()

    except Exception:
        error_message = "Critical Error occurred, trying to start a new instance..."
        print(error_message)
        time.sleep(5)
        create_instance()


if __name__ == "__main__":
    os.system("cls")
    create_instance()
