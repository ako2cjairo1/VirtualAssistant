@ECHO OFF
netsh interface set interface "Wi-Fi" enable
@ECHO **Enabling the Wi-fi...
TIMEOUT 3
EXIT