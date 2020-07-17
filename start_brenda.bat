@ECHO OFF
CMDOW @ /ren "Virtual Assistant - Brenda" /mov 1174 533 /siz 217 203 /top
CD C:\Users\Dave\DEVENV\Python\VirtualAssistant
CLS
python main.py
@ECHO Virtual Assistant is closing...
TIMEOUT 1
EXIT