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

    print("Parser input:", text)

    prompt = f"""
Extract user information from this speech transcript.

Return JSON with exactly these fields:
- name
- email
- action
- user_id

Rules:

1. action must be "create" or "update".
2. Extract the actual person's name.
3. Extract the actual email.
4. Do NOT include words like "and", "my", "email", "is" in the name.
5. Spoken email variations must be understood.

Examples of spoken @:
- at
- at the rate
- at rate
- at the red
- at the raet

Examples of spoken dot:
- dot
- period
- point

Examples:

"My name is Neha and my email is neha at gmail dot com"

Return:
{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null
}}

"My name is Neha and my email is neha at the rate gmail dot com"

Return:
{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null
}}

"My name is Neha and my email is neha at the red gmail dot com"

Return:
{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null
}}

"Update user 5. Change my name to Raj and my email to raj at gmail dot com"

Return:
{{
    "name": "Raj",
    "email": "raj@gmail.com",
    "action": "update",
    "user_id": 5
}}

IMPORTANT:
- Do not guess missing information.
- If name cannot be determined, use null.
- If email cannot be determined, use null.
- Return ONLY valid JSON.

Transcript:
{text}
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
            temperature=0,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content.strip()

        data = json.loads(result)

        action = data.get("action", "create").lower()

        user = {
            "name": data.get("name"),
            "email": data.get("email"),
            "action": action
        }

        if action == "update" and data.get("user_id") is not None:
            user["id"] = int(data["user_id"])

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