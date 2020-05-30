import speech_recognition as sr
import os
import random
import playsound
from gtts import gTTS


def listen_to_audio(ask=False):
    with sr.Microphone() as source:
        r = sr.Recognizer()
        # one-time calibration of microphone
        r.adjust_for_ambient_noise(source)

        if ask:
            speak(ask)

        audio = r.listen(source)
        voice_data = ""
        try:
            voice_data = r.recognize_google(audio)
        except sr.UnknownValueError:
            return voice_data
        except sr.RequestError:
            speak("Sorry, my speech service is not available at the moment")
        print(voice_data)
        return voice_data


def speak(audio_string):
    if audio_string:
        tts = gTTS(text=audio_string, lang="en", slow=False)
        rand = random.randint(1, 1000)
        audio_file = "audio-" + str(rand) + ".mp3"
        tts.save(audio_file)
        print(audio_string)
        playsound.playsound(audio_file)
        os.remove(audio_file)
