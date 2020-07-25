@ECHO OFF
CMDOW @ /ren "Virtual Assistant - Brenda" /mov 900 400 /siz 491 336 /top
CD C:\Users\Dave\DEVENV\Python\VirtualAssistant
CLS
python main.py
@ECHO Virtual Assistant is closing...
TIMEOUT 1
EXIT