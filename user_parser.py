import re


def normalize_email(email):
    if not email:
        return None

    email = email.lower().strip()

    # Common speech-to-text variations
    email = re.sub(r"\s+at\s+", "@", email)
    email = re.sub(r"\s+dot\s+", ".", email)

    # Handle "at" / "dot" without perfect spacing
    email = email.replace(" at ", "@")
    email = email.replace(" dot ", ".")

    # Remove spaces around @ and .
    email = re.sub(r"\s*@\s*", "@", email)
    email = re.sub(r"\s*\.\s*", ".", email)

    # Remove remaining spaces inside email
    email = re.sub(r"\s+", "", email)

    return email


def extract_email(text):
    """
    Extract email from normal email or spoken email.
    Examples:
    raj@gmail.com
    raj at gmail dot com
    raj at gmail.com
    raj gmail dot com
    """

    text = text.lower()

    # Normal email: raj@gmail.com
    match = re.search(
        r"[\w.-]+@[\w.-]+\.[a-z]{2,}",
        text
    )

    if match:
        return normalize_email(match.group(0))

    # Spoken email:
    # raj at gmail dot com
    match = re.search(
        r"[\w.-]+\s+at\s+[\w.-]+(?:\s+dot\s+|\.)[a-z]{2,}",
        text
    )

    if match:
        return normalize_email(match.group(0))

    # "raj at gmail com"
    match = re.search(
        r"[\w.-]+\s+at\s+[\w.-]+\s+(?:dot\s+)?[a-z]{2,}",
        text
    )

    if match:
        email = match.group(0)

        # If "dot" was missed by transcription
        parts = re.split(r"\s+at\s+", email)

        if len(parts) == 2:
            username = parts[0].strip()
            domain = parts[1].strip().replace(" ", "")

            # Common domain handling
            if "." not in domain:
                common_domains = {
                    "gmailcom": "gmail.com",
                    "yahoo": "yahoo.com",
                    "hotmail": "hotmail.com",
                    "outlook": "outlook.com"
                }

                domain = common_domains.get(
                    domain,
                    domain
                )

            return normalize_email(
                f"{username}@{domain}"
            )

    return None


def extract_name(text):
    """
    Extract name even if small connecting words
    like 'is', 'my', or 'and' are missing.
    """

    # Normal:
    # my name is Raj
    match = re.search(
        r"my\s+name\s+(?:is\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    # Update:
    # change my name to Raj Kumar
    match = re.search(
        r"change\s+my\s+name\s+(?:to\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    # Handles transcript:
    # "my name Raj"
    match = re.search(
        r"name\s+(?:is\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def parse_user(text):

    if not text:
        return {
            "name": None,
            "email": None,
            "action": "create"
        }

    # Check UPDATE command
    update_match = re.search(
        r"update\s+user\s+(\d+)",
        text,
        re.IGNORECASE
    )

    name = extract_name(text)
    email = extract_email(text)

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