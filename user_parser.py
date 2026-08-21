import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# NORMALIZE SPOKEN EMAIL
# =========================================================

def normalize_spoken_email(value):

    if not value:
        return None

    email = value.strip().lower()

    # Remove common ending punctuation
    email = re.sub(r"[.!?,]+$", "", email)

    # Convert spoken @ variations
    email = re.sub(
        r"\s+at\s+the\s+rate\s+",
        "@",
        email
    )

    email = re.sub(
        r"\s+at\s+rate\s+",
        "@",
        email
    )

    email = re.sub(
        r"\s+at\s+the\s+red\s+",
        "@",
        email
    )

    email = re.sub(
        r"\s+at\s+red\s+",
        "@",
        email
    )

    email = re.sub(
        r"\s+at\s+the\s+raet\s+",
        "@",
        email
    )

    email = re.sub(
        r"\s+at\s+",
        "@",
        email
    )

    # Convert spoken dot variations
    email = re.sub(
        r"\s+(?:dot|period|point)\s+",
        ".",
        email
    )

    # Remove remaining spaces
    email = re.sub(
        r"\s+",
        "",
        email
    )

    return email


def parse_user(text):

    if not text:
        return {
            "name": None,
            "email": None,
            "action": "create",
            "email_confident": False
        }

    print("Parser input:", text)

    clean_text = re.sub(
        r"\s+",
        " ",
        text.strip()
    )

    clean_text = re.sub(
        r"[.!?]+$",
        "",
        clean_text
    ).strip()

    # =========================================================
    # NORMALIZE "SO" -> "SHOW"
    # =========================================================

    show_text = re.sub(
        r"^\s*so\s+",
        "show ",
        clean_text,
        flags=re.IGNORECASE
    )

    # =========================================================
    # SHOW ALL USERS / DETAILS
    # =========================================================

    if re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?"
        r"(?:user|users)?\s*details?\s*$",
        show_text,
        re.IGNORECASE
    ):

        return {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False
        }

    if re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?users?\s*$",
        show_text,
        re.IGNORECASE
    ):

        return {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False
        }

    # =========================================================
    # SHOW BY USER ID
    # =========================================================

    show_user_id_match = re.search(
        r"^\s*show\s+(?:me\s+)?user\s+(\d+)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_user_id_match:

        return {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False,
            "id": int(show_user_id_match.group(1))
        }

    # =========================================================
    # SHOW USER WITH EMAIL
    # =========================================================
    #
    # Examples:
    #
    # Show user with email neha@gmail.com
    # Show user with email neha at gmail dot com
    # Show user with email neha at the rate gmail dot com
    # Show user with email neha at the red gmail dot com
    #
    # Also handles when Whisper drops "show":
    #
    # User with email neha at the rate gmail dot com

    show_email_phrase_match = re.search(
        r"^\s*(?:show\s+)?"
        r"(?:user\s+)?with\s+email\s+"
        r"(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_email_phrase_match:

        raw_email = show_email_phrase_match.group(1).strip()

        email = normalize_spoken_email(raw_email)

        if email and "@" in email:

            return {
                "name": None,
                "email": email,
                "action": "show",
                "email_confident": True
            }

    # =========================================================
    # SHOW DIRECT EMAIL
    # =========================================================
    #
    # Show neha@gmail.com

    direct_email_match = re.search(
        r"^\s*show\s+"
        r"([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})\s*$",
        show_text,
        re.IGNORECASE
    )

    if direct_email_match:

        return {
            "name": None,
            "email": direct_email_match.group(1).lower(),
            "action": "show",
            "email_confident": True
        }

    # =========================================================
    # SHOW SPOKEN EMAIL
    # =========================================================
    #
    # Show neha at gmail dot com
    # Show neha at the rate gmail dot com
    # Show neha at the red gmail dot com
    #
    # Also supports:
    # Show neha at gmail.com

    spoken_email_match = re.search(
        r"^\s*show\s+(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if spoken_email_match:

        possible_email = normalize_spoken_email(
            spoken_email_match.group(1)
        )

        if (
            possible_email
            and "@" in possible_email
            and "." in possible_email.split("@")[-1]
        ):

            return {
                "name": None,
                "email": possible_email,
                "action": "show",
                "email_confident": True
            }

    # =========================================================
    # SHOW DETAILS OF NAME
    # =========================================================

    show_details_match = re.search(
        r"^\s*show\s+(?:me\s+)?(?:the\s+)?details?\s+"
        r"(?:of|for)\s+(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_details_match:

        return {
            "name": show_details_match.group(1).strip(),
            "email": None,
            "action": "show",
            "email_confident": False
        }

    # =========================================================
    # SHOW USERS BY NAME
    # =========================================================

    show_named_match = re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?users?\s+"
        r"(?:named|with\s+the\s+name)\s+(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_named_match:

        return {
            "name": show_named_match.group(1).strip(),
            "email": None,
            "action": "show",
            "email_confident": False
        }

    # =========================================================
    # SHOW NAME DIRECTLY
    # =========================================================

    direct_show_name_match = re.search(
        r"^\s*show\s+([A-Za-z][A-Za-z\s.-]*)\s*$",
        show_text,
        re.IGNORECASE
    )

    if direct_show_name_match:

        name = direct_show_name_match.group(1).strip()

        if name.lower() not in [
            "user",
            "users",
            "details"
        ]:

            return {
                "name": name,
                "email": None,
                "action": "show",
                "email_confident": False
            }

    # =========================================================
    # CREATE / UPDATE LLM
    # =========================================================

    prompt = f"""
You are an AI system that extracts user information from voice transcripts.

Extract:

- name
- email
- action: create or update
- user_id for update

SHOW commands are handled separately.
Only extract CREATE or UPDATE commands here.

IMPORTANT EMAIL RULES:

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

6. Never create fake information.

7. For UPDATE, extract the user ID if provided.

8. Return ONLY valid JSON.

Expected CREATE:

{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null,
    "email_confident": true
}}

Expected UPDATE:

{{
    "name": "Raj",
    "email": "raj@gmail.com",
    "action": "update",
    "user_id": 5,
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
{clean_text}
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
            response_format={
                "type": "json_object"
            }
        )

        result = response.choices[0].message.content.strip()

        data = json.loads(result)

        # IMPORTANT:
        # Prevent NoneType .lower() error
        action = (
            data.get("action") or "create"
        ).lower()

        if action not in [
            "create",
            "update"
        ]:

            action = "create"

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

                try:
                    user["id"] = int(user_id)

                except (ValueError, TypeError):

                    user["id"] = None

        # =====================================================
        # EMAIL SAFETY
        # =====================================================

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


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    test_cases = [
        "Show neha@gmail.com",
        "Show neha at gmail dot com",
        "Show neha at the rate gmail dot com",
        "Show neha at the red gmail dot com",
        "Show user with email neha at the rate gmail dot com",
        "User with email neha at the rate gmail dot com",
        "So neha at gmail dot com",
        "Show user 29",
        "Show Neha"
    ]

    for test_text in test_cases:

        print("\n" + "=" * 60)
        print("TEST:")
        print(test_text)

        result = parse_user(test_text)

        print("RESULT:")
        print(result)