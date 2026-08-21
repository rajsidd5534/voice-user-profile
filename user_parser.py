import os
import json
import re

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

    # =========================================================
    # NORMALIZE SPEECH-TO-TEXT
    # =========================================================

    clean_text = re.sub(
        r"\s+",
        " ",
        text.strip()
    )

    # Remove punctuation from the end
    #
    # Example:
    # Show user details.
    # Show user details!
    # Show user details?
    #
    # becomes:
    # Show user details

    clean_text = re.sub(
        r"[.!?]+$",
        "",
        clean_text
    ).strip()

    # =========================================================
    # SHOW COMMAND NORMALIZATION
    # =========================================================
    #
    # Whisper can sometimes transcribe:
    #
    # "Show user details"
    # as
    # "So user details"
    #
    # or:
    # "So, user details"
    #
    # We only convert "so" when it is at the beginning
    # and is followed by a SHOW-related command.
    #
    # CREATE / UPDATE commands are not affected.

    show_text = re.sub(
        r"^\s*so\s*,?\s+",
        "show ",
        clean_text,
        flags=re.IGNORECASE
    )

    # =========================================================
    # SHOW USER DETAILS
    # =========================================================

    if re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?(?:user\s+)?details?\s*$",
        show_text,
        re.IGNORECASE
    ):

        user = {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # SHOW ALL USERS
    # =========================================================

    if re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?users?\s*$",
        show_text,
        re.IGNORECASE
    ):

        user = {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # SHOW DETAILS OF NAME
    # =========================================================
    #
    # Examples:
    #
    # Show details of Raj
    # Show details for Raj
    # Show me details of Neha
    # So details of Raj

    show_details_match = re.search(
        r"^\s*show\s+(?:me\s+)?(?:the\s+)?details?\s+"
        r"(?:of|for)\s+(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_details_match:

        name = show_details_match.group(1).strip()

        user = {
            "name": name,
            "email": None,
            "action": "show",
            "email_confident": False
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # SHOW NAME'S DETAILS
    # =========================================================
    #
    # Examples:
    #
    # Show Raj's details
    # Show Neha's details
    # Show Raj's user details
    # So Raj's details

    show_name_details_match = re.search(
        r"^\s*show\s+(?:me\s+)?(.+?)['’]s\s+"
        r"(?:user\s+)?details?\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_name_details_match:

        name = show_name_details_match.group(1).strip()

        user = {
            "name": name,
            "email": None,
            "action": "show",
            "email_confident": False
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # SHOW USERS BY NAME
    # =========================================================
    #
    # Examples:
    #
    # Show users named Raj
    # Show all users named Raj
    # Show users with the name Raj
    # So users named Raj

    show_named_match = re.search(
        r"^\s*show\s+(?:me\s+)?(?:all\s+)?users?\s+"
        r"(?:named|with\s+the\s+name)\s+(.+?)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_named_match:

        name = show_named_match.group(1).strip()

        user = {
            "name": name,
            "email": None,
            "action": "show",
            "email_confident": False
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # SHOW USER BY ID
    # =========================================================
    #
    # Examples:
    #
    # Show user 39
    # Show me user 39
    # So user 39

    show_user_id_match = re.search(
        r"^\s*show\s+(?:me\s+)?user\s+(\d+)\s*$",
        show_text,
        re.IGNORECASE
    )

    if show_user_id_match:

        user_id = int(
            show_user_id_match.group(1)
        )

        user = {
            "name": None,
            "email": None,
            "action": "show",
            "email_confident": False,
            "id": user_id
        }

        print("Parsed SHOW User:")
        print(user)

        return user

    # =========================================================
    # CREATE / UPDATE
    # =========================================================

    prompt = f"""
You are an AI system that extracts user information from voice transcripts.

Extract:

- name
- email
- action: create or update
- user_id for update

IMPORTANT:

SHOW commands are already handled by the application.
You only need to extract CREATE or UPDATE commands here.

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

8. For UPDATE, extract the user ID if it is provided.

9. Return ONLY valid JSON.

Expected CREATE JSON:

{{
    "name": "Neha",
    "email": "neha@gmail.com",
    "action": "create",
    "user_id": null,
    "email_confident": true
}}

Expected UPDATE JSON:

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

        action = data.get(
            "action",
            "create"
        ).lower()

        # Only CREATE and UPDATE are allowed
        # from the LLM.
        if action not in ["create", "update"]:
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

        # =====================================================
        # UPDATE USER ID
        # =====================================================

        if action == "update":

            user_id = data.get("user_id")

            if user_id is not None:

                try:
                    user["id"] = int(user_id)

                except (ValueError, TypeError):

                    user["id"] = None

        # =====================================================
        # EMAIL SAFETY CHECK
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


# =============================================================
# LOCAL TEST
# =============================================================

if __name__ == "__main__":

    test_cases = [

        "Show user details.",

        "So user details.",

        "So, user details.",

        "Show all users.",

        "So all users.",

        "Show details of Raj.",

        "So details of Raj.",

        "Show Raj's details.",

        "So Raj's details.",

        "Show user 39.",

        "So user 39.",

        "Create a new user. "
        "My name is Neha and my email is "
        "neha at the red gmail dot com.",

        "Update user 39. "
        "Change my name to Nisha Kumari and "
        "my email to nisha12 at gmail dot com."
    ]

    for test_text in test_cases:

        print("\n" + "=" * 60)
        print("TEST:")
        print(test_text)

        result = parse_user(test_text)

        print("RESULT:")
        print(result)