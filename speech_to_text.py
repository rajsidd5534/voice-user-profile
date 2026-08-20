from faster_whisper import WhisperModel


model = WhisperModel(
    "tiny.en",
    device="cpu",
    compute_type="int8",
    cpu_threads=1,
    num_workers=1
)


def transcribe_audio(audio_file):
    segments, info = model.transcribe(
        audio_file,
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False
    )

    text = " ".join(segment.text for segment in segments)

    return text.strip()


if __name__ == "__main__":
    print("Speech-to-text module is ready.")