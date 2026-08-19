from faster_whisper import WhisperModel
from user_parser import parse_user


model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)


def transcribe_audio(audio_file):
    segments, info = model.transcribe(audio_file)

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip()


if __name__ == "__main__":
    text = transcribe_audio("audio/user_voice.m4a")

    print("\nTranscribed Text:")
    print(text)

    user = parse_user(text)

    print("\nUser Profile:")
    print("Name:", user["name"])
    print("Email:", user["email"])