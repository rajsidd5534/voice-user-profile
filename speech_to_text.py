from faster_whisper import WhisperModel


# Load Whisper model
model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)


def transcribe_audio(audio_file):
    segments, info = model.transcribe(
        audio_file,
        beam_size=1,
        vad_filter=True
    )

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()


if __name__ == "__main__":
    print("Speech-to-text module is ready.")