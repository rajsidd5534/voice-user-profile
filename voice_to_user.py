import requests

from speech_to_text import transcribe_audio
from user_parser import parse_user


def process_voice(audio_file):
    # 1. Voice -> Text
    text = transcribe_audio(audio_file)

    print("\nTranscribed Text:")
    print(text)

    # 2. Text -> User Profile
    user = parse_user(text)

    print("\nExtracted User:")
    print(user)

    action = user.get("action")

    # Data that will be sent to API
    user_data = {
        "name": user.get("name"),
        "email": user.get("email")
    }

    # 3. Create User
    if action == "create":
        response = requests.post(
            "http://127.0.0.1:7000/users",
            json=user_data
        )

    # 4. Update User
    elif action == "update":
        user_id = user.get("id")

        response = requests.put(
            f"http://127.0.0.1:7000/users/{user_id}",
            json=user_data
        )

    else:
        print("\nUnknown action.")
        return

    print("\nAPI Response:")
    print("Status:", response.status_code)
    print(response.json())


if __name__ == "__main__":
    process_voice("audio/user_voice.m4a")