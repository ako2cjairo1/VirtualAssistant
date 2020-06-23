
def is_match(voice_data, keywords):
    lowercase_keywords = [x.lower().strip() for x in keywords]
    if (any(map(lambda word: word.lower().strip() in voice_data, lowercase_keywords))):
        return True
    return False


def clean_voice_data(voice_data, assistants_name):
    clean_data = voice_data

    # if not greeting_commands(voice_data):
    if voice_data.lower().find(assistants_name.lower()) > 0:
        # remove all words starting from assistant's name
        clean_data = voice_data[(voice_data.lower().find(
            assistants_name.lower()) + len(assistants_name)):].strip()

        # if assitant name's the last word in sentence
        if len(clean_data.split(" ")) <= 1:
            # remove only the portion of assistant's name in voice_data
            clean_data = voice_data.replace(
                assistants_name.lower(), "").strip()

    return clean_data


def extract_metadata(voice_data, commands):
    meta_keyword = voice_data
    extracted = True

    for command in commands:
        # remove the first occurance of command from voice data
        if command.lower().strip() in voice_data.lower():
            extracted = False
            meta_keyword = voice_data[(voice_data.find(
                command.lower().strip()) + len(command)):].strip()
            # apply recursion until we extracted the meta_data
            return extract_metadata(meta_keyword, commands)

    if extracted:
        # # set to original voice_data if no meta_keword was found
        if not meta_keyword:
            meta_keyword = voice_data
        return meta_keyword
