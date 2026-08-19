import re


def normalize_email(email):
    if not email:
        return None

    email = email.lower().strip()

    # "at" -> "@"
    email = re.sub(r"\s+at\s+", "@", email)

    # "dot" -> "."
    email = re.sub(r"\s+dot\s+", ".", email)

    # Remove spaces around @ and .
    email = re.sub(r"\s*@\s*", "@", email)
    email = re.sub(r"\s*\.\s*", ".", email)

    return email


def parse_user(text):

    # Check UPDATE command
    update_match = re.search(
        r"update user\s+(\d+)",
        text,
        re.IGNORECASE
    )

    # Extract name
    name_match = re.search(
        r"(?:my name is|change my name to)\s+([A-Za-z ]+?)(?:\s+and|\s+my email|$)",
        text,
        re.IGNORECASE
    )

    # Extract email
    email_match = re.search(
        r"[\w.-]+\s*(?:at|@)\s*[\w.-]+\s*(?:dot|\.)\s*\w+",
        text,
        re.IGNORECASE
    )

    name = name_match.group(1).strip() if name_match else None

    email = email_match.group(0).strip() if email_match else None

    email = normalize_email(email)

    user = {
        "name": name,
        "email": email
    }

    if update_match:
        user["id"] = int(update_match.group(1))
        user["action"] = "update"
    else:
        user["action"] = "create"

    return user