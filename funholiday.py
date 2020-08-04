import os
from settings import Configuration

settings = Configuration()


def toast_notification(title, message, duration=600):
    try:
        import sys
        sys.path.append(settings.UTILS_DIR)
        from send_toast import ToastMessage
        notification = ToastMessage()
        # change the directory to location of batch file to execute
        os.chdir(settings.UTILS_DIR)

        notification.send_toast(title, message, duration=duration)
        # self.tts.respond_to_bot(f"‼️ {title} ‼️")
        # self.tts.respond_to_bot(message)

        # get back to virtual assistant directory
        os.chdir(settings.ASSISTANT_DIR)

    except Exception:
        print("Toast Notification Skill Error.")


try:
    import sys
    sys.path.append(settings.NEWS_DIR)
    from FunHolidays import FunHoliday
    fh = FunHoliday()
    # change the directory to location of batch file to execute
    os.chdir(settings.NEWS_DIR)

    result = fh.get_fun_holiday()
    if result["success"] == "true":
        holiday = result["holiday"]

        title = f'Today is \"{holiday["title"]}\"'
        message = holiday["did you know"]

        print(message)
        # toast_notification(title, message, duration=300)
        # print(f'Date: {holiday["date"]}\nTitle: {holiday["title"]}\nHeading: {holiday["heading"]}\nDid You Know? {holiday["did you know"]}\nURL: {holiday["source url"]}')
    else:
        print(result["message"])

    # get back to virtual assistant directory
    os.chdir(settings.ASSISTANT_DIR)

except Exception as ex:
    print(f"Fun Holiday Skill Error. {str(ex)}")
exit()
