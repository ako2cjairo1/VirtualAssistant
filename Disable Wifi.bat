@ECHO OFF
netsh interface set interface "Wi-Fi" disabled
@ECHO **Disabling the Wi-fi...
TIMEOUT 3
EXIT