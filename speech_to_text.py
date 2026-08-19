from faster_whisper import WhisperModel
from user_parser import parse_user

model = WhisperModel(
    "tiny",
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
    print("speech_to_text module is ready.")