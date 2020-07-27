import os
from assitant import VirtualAssistant

if __name__ == "__main__":
    os.system("cls")
    brenda = VirtualAssistant(masters_name="Dave", assistants_name="Brenda", listen_timeout=10)
    brenda.maximize_command_interface()
    brenda.activate()
