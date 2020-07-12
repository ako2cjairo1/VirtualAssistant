import os
import wolframalpha
import sys
# import weathercom
from assitant import VirtualAssistant


WOLFRAM_APP_ID = os.environ.get("WOLFRAM_APP_ID")

if __name__ == "__main__":
    os.system("cls")
    os.system("CMDOW @ /ren \"Virtual Assistant - Brenda\" /mov 1174 533 /siz 217 203 /top")
    brenda = VirtualAssistant(masters_name="Dave", assistants_name="Brenda", listen_timeout=10)
    brenda.activate()
    # print(weathercom.getCityWeatherDetails(city="Malolos, Bulacan", queryType="daily-data"))
