
import re


def extract_ranking(question):

    question = question.lower()
    question = re.sub(r"\s+", " ", question).strip()

    # 1. Explicit Top N
    match = re.search(r"\btop\s*(\d+)?\b", question)

    if match:
        return {
            "enabled": True,
            "order": "DESC",
            "top_n": int(match.group(1)) if match.group(1) else 1
        }

    # 2. Explicit Bottom N
    match = re.search(r"\bbottom\s*(\d+)?\b", question)

    if match:
        return {
            "enabled": True,
            "order": "ASC",
            "top_n": int(match.group(1)) if match.group(1) else 1
        }

    # 3. Number before a dimension:
    #    "3 vehicles with the most dispatches"
    #    "10 districts by abandoned cases"
    match = re.search(
        r"\b(\d+)\s+"
        r"(?:vehicles?|districts?|regions?|base locations?)\b"
        r"(?=.*\b(?:most|highest|lowest|least|by)\b)",
        question
    )

    if match:
        return {
            "enabled": True,
            "order": (
                "ASC"
                if re.search(r"\b(?:lowest|least)\b", question)
                else "DESC"
            ),
            "top_n": int(match.group(1))
        }

    # 4. Highest / Most
    if re.search(r"\b(highest|most|max|maximum)\b", question):
        return {
            "enabled": True,
            "order": "DESC",
            "top_n": 1
        }

    # 5. Lowest / Least
    if re.search(r"\b(lowest|least|min|minimum)\b", question):
        return {
            "enabled": True,
            "order": "ASC",
            "top_n": 1
        }

    return {
        "enabled": False,
        "order": None,
        "top_n": None
    }
