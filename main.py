import os
from assitant import VirtualAssistant

if __name__ == "__main__":
    os.system("cls")
    os.system("CMDOW @ /ren \"Virtual Assistant - Brenda\" /mov 1174 533 /siz 217 203 /top")
    
    brenda = VirtualAssistant(masters_name="Dave", assistants_name="Brenda", listen_timeout=10)
    brenda.activate()