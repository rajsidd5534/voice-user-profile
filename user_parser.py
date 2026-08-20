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
            "action": "create",
            "email_confident": False
        }

    print("Parser input:", text)

    prompt = f"""
You are an AI system that extracts user information from voice transcripts.

Extract:

- name
- email
- action: create or update
- user_id for update

IMPORTANT EMAIL RULES:

People speak emails differently.

Understand these as "@":
- at
- at the rate
- at rate
- at the red
- at red
- at the raet
- similar speech-to-text mistakes

Understand these as ".":
- dot
- period
- point

Examples:

"My name is Neha and my email is neha at gmail dot com"
=> neha@gmail.com

"My name is Neha and my email is neha at the rate gmail dot com"
=> neha@gmail.com

"My name is Neha and my email is neha at the red gmail dot com"
=> neha@gmail.com

"My name is Raj and my email is raj at yahoo dot com"
=> raj@yahoo.com

IMPORTANT:

1. Do NOT include "and", "my", "email", or "is" inside the name.

2. Correct obvious speech-to-text mistakes when the intended email is clear.

3. Do NOT invent an email when the transcript is ambiguous.

4. If the email cannot be confidently determined, return:
   "email": null
   "email_confident": false

5. If the email is clearly understood, return:
   "email_confident": true

6. If someone says something like:
   "my email is nehagmail.com"
   and you cannot confidently determine the intended email,
   DO NOT convert it into a guessed email.

7. Never create fake information.

8. Return ONLY valid JSON.

Expected JSON format:

{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null,
    "email_confident": true
}}

If email is unclear:

{{
    "name": "Neha",
    "email": null,
    "action": "create",
    "user_id": null,
    "email_confident": false
}}

Transcript:
{text}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured user information "
                        "from speech transcripts."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content.strip()

        data = json.loads(result)

        action = data.get("action", "create").lower()

        user = {
            "name": data.get("name"),
            "email": data.get("email"),
            "action": action,
            "email_confident": data.get(
                "email_confident",
                False
            )
        }

        if action == "update":

            user_id = data.get("user_id")

            if user_id is not None:
                user["id"] = int(user_id)

        # -----------------------------------------
        # Safety check
        # -----------------------------------------

        if not user["email_confident"]:
            user["email"] = None

        print("LLM Parsed User:")
        print(user)

        return user

    except Exception as e:

        print("LLM Parser Error:", e)

        return {
            "name": None,
            "email": None,
            "action": "create",
            "email_confident": False
        }


if __name__ == "__main__":

    test_text = (
        "Create a new user. "
        "My name is Neha and my email is "
        "neha at the red gmail dot com."
    )

    print(parse_user(test_text))