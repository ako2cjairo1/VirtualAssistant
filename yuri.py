
import tts
import yuri_responses
from time import ctime


if __name__ == "__main__":
    print("START")

    yuri = yuri_responses.YuriResponse()

    waiting_time = 0
    while True:
        print(f"{waiting_time} - {ctime()}")

        if waiting_time == 3:
            waiting_time = 0
        elif yuri.wake_yuri(waiting_time):
            print("Listening...")
            voice_data = tts.listen_to_audio()
            if voice_data:
                yuri.formulate_responses(voice_data)
                waiting_time -= 1

            waiting_time += 1
        else:
            print("Sleeping..." + str(waiting_time))

    print("END")
