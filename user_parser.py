import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def parse_user(text):

    if not text:
        return {
            "name": None,
            "email": None,
            "action": "create"
        }

    prompt = f"""
You are a user information extraction system.

Extract the following information from the speech transcript:

1. action: "create" or "update"
2. name
3. email
4. user_id if the action is update

The transcript may contain:
- different accents
- missing connecting words
- spoken email formats
- speech-to-text mistakes
- "at", "at the rate", "at the red", "at rate" meaning "@"
- "dot", "period", "point" meaning "."
- "gmail" should remain gmail.com when appropriate

Examples:

"my name is Neha and my email is neha at gmail dot com"
=> name: Neha
=> email: neha@gmail.com

"my name is Neha and my email is neha at the rate gmail dot com"
=> name: Neha
=> email: neha@gmail.com

"my name is Neha and my email is neha at the red gmail dot com"
=> name: Neha
=> email: neha@gmail.com

"update user 5, change my name to Raj and email to raj at gmail dot com"
=> action: update
=> user_id: 5
=> name: Raj
=> email: raj@gmail.com

IMPORTANT:
- Do not invent a name or email.
- If the information cannot be reliably determined, return null.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.

Transcript:
{text}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured user information from speech transcripts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        result = response.choices[0].message.content.strip()

        # Remove accidental markdown fences
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        data = json.loads(result)

        action = data.get("action", "create").lower()

        user = {
            "name": data.get("name"),
            "email": data.get("email"),
            "action": action
        }

        if action == "update":
            user_id = data.get("user_id")

            if user_id is not None:
                user["id"] = int(user_id)

        print("LLM Parsed User:")
        print(user)

        return user

    except Exception as e:

        print("LLM Parser Error:", e)

        return {
            "name": None,
            "email": None,
            "action": "create"
        }


if __name__ == "__main__":

    test_text = (
        "Create a new user. "
        "My name is Neha and my email is "
        "neha at the red gmail dot com."
    )

    print(parse_user(test_text))