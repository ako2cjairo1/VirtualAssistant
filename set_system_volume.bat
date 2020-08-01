@ECHO OFF
CD C:\Users\Dave\DEVENV\Python\VirtualAssistant
CLS
SET volume=%1
@ECHO Setting the volume to %volume%
python pycaw_volume.py --volume %volume%
TIMEOUT 3
EXIT
