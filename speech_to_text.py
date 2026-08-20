import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def transcribe_audio(audio_file):

    with open(audio_file, "rb") as file:

        transcription = client.audio.transcriptions.create(
            file=("voice.webm", file.read()),
            model="whisper-large-v3-turbo",
            language="en",
            response_format="json",
            temperature=0
        )

    return transcription.text.strip()


if __name__ == "__main__":
    print("Groq speech-to-text is ready.")