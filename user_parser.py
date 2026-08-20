import re


# -----------------------------------------
# EMAIL NORMALIZATION
# -----------------------------------------

def normalize_email(email):
    if not email:
        return None

    email = email.lower().strip()

    # Spoken variations
    email = re.sub(r"\bat\s+the\s+rate\b", "@", email)
    email = re.sub(r"\bat\s+rate\b", "@", email)
    email = re.sub(r"\bat\s+the\b", "@", email)
    email = re.sub(r"\bat\b", "@", email)

    # Spoken dot
    email = re.sub(r"\bdot\b", ".", email)

    # Remove spaces around @ and .
    email = re.sub(r"\s*@\s*", "@", email)
    email = re.sub(r"\s*\.\s*", ".", email)

    # Remove remaining spaces
    email = re.sub(r"\s+", "", email)

    return email


# -----------------------------------------
# EMAIL VALIDATION
# -----------------------------------------

def is_valid_email(email):
    if not email:
        return False

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.fullmatch(pattern, email) is not None


# -----------------------------------------
# EXTRACT EMAIL
# -----------------------------------------

def extract_email(text):

    text = text.lower().strip()

    # -------------------------------------
    # Normal email
    # neha@gmail.com
    # -------------------------------------

    match = re.search(
        r"[\w.-]+@[\w.-]+\.[a-z]{2,}",
        text,
        re.IGNORECASE
    )

    if match:
        email = normalize_email(match.group(0))

        if is_valid_email(email):
            return email

    # -------------------------------------
    # Spoken email
    #
    # neha at gmail dot com
    # neha at the rate gmail dot com
    # neha at the gmail dot com
    # -------------------------------------

    spoken_pattern = (
        r"[\w.-]+"
        r"\s+"
        r"(?:at\s+(?:the\s+)?(?:rate\s+)?)"
        r"[\w.-]+"
        r"\s+dot\s+"
        r"[a-z]{2,}"
    )

    match = re.search(
        spoken_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        email = normalize_email(match.group(0))

        if is_valid_email(email):
            return email

    # -------------------------------------
    # neha at gmail.com
    # -------------------------------------

    match = re.search(
        r"[\w.-]+\s+at\s+[\w.-]+\.[a-z]{2,}",
        text,
        re.IGNORECASE
    )

    if match:
        email = normalize_email(match.group(0))

        if is_valid_email(email):
            return email

    return None


# -----------------------------------------
# EXTRACT NAME
# -----------------------------------------

def extract_name(text):

    text = text.strip()

    # -------------------------------------
    # My name is Neha and my email is...
    # -------------------------------------

    match = re.search(
        r"\bmy\s+name\s+is\s+(.+?)(?=\s+and\s+my\s+email\b|\s+my\s+email\b|\s+email\b|$)",
        text,
        re.IGNORECASE
    )

    if match:
        name = match.group(1).strip()

        # Extra protection
        name = re.sub(
            r"\s+and\s*$",
            "",
            name,
            flags=re.IGNORECASE
        )

        return name.strip()

    # -------------------------------------
    # My name Neha and my email...
    # -------------------------------------

    match = re.search(
        r"\bmy\s+name\s+(.+?)(?=\s+and\s+my\s+email\b|\s+my\s+email\b|\s+email\b|$)",
        text,
        re.IGNORECASE
    )

    if match:
        name = match.group(1).strip()

        name = re.sub(
            r"\s+and\s*$",
            "",
            name,
            flags=re.IGNORECASE
        )

        return name.strip()

    # -------------------------------------
    # Change my name to Raj Kumar and...
    # -------------------------------------

    match = re.search(
        r"\bchange\s+my\s+name\s+to\s+(.+?)(?=\s+and\s+my\s+email\b|\s+my\s+email\b|\s+email\b|$)",
        text,
        re.IGNORECASE
    )

    if match:
        name = match.group(1).strip()

        name = re.sub(
            r"\s+and\s*$",
            "",
            name,
            flags=re.IGNORECASE
        )

        return name.strip()

    return None


# -----------------------------------------
# MAIN PARSER
# -----------------------------------------

def parse_user(text):

    if not text:
        return {
            "name": None,
            "email": None,
            "action": "create"
        }

    print("Parser input:", text)

    # -------------------------------------
    # Check UPDATE
    # -------------------------------------

    update_match = re.search(
        r"\bupdate\s+user\s+(\d+)\b",
        text,
        re.IGNORECASE
    )

    # -------------------------------------
    # Extract
    # -------------------------------------

    name = extract_name(text)
    email = extract_email(text)

    user = {
        "name": name,
        "email": email
    }

    # -------------------------------------
    # Action
    # -------------------------------------

    if update_match:
        user["id"] = int(update_match.group(1))
        user["action"] = "update"
    else:
        user["action"] = "create"

    print("Parsed User:", user)

    return user