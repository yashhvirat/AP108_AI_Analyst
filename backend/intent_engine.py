
import re
from datetime import datetime

from backend.metric_engine import METRICS
from backend.dimension_map import DIMENSION_MAP


def load_dimensions():
    return {
        config["reference"]
        for config in DIMENSION_MAP.values()
    }


def parse_date(value):
    formats = [
        "%d %b %Y",
        "%d %B %Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None




def extract_date_filter(question):

    patterns = [
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\b",
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    formats = [
        "%d %b %Y",
        "%d %B %Y",
        "%d %b",
        "%d %B",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    matches = []

    for pattern in patterns:

        for match in re.finditer(pattern, question, re.IGNORECASE):

            matches.append({
                "text": match.group().strip(),
                "start": match.start(),
                "end": match.end()
            })

    # Remove duplicate or overlapping matches.
    unique_matches = []

    for item in sorted(matches, key=lambda x: (x["start"], -(x["end"] - x["start"]))):

        if not any(
            item["start"] < existing["end"]
            and item["end"] > existing["start"]
            for existing in unique_matches
        ):
            unique_matches.append(item)

    dates = []

    for item in unique_matches:

        parsed = None

        for fmt in formats:
            try:
                parsed = datetime.strptime(item["text"], fmt).date()
                break
            except ValueError:
                continue

        if parsed:
            dates.append({
                "date": parsed,
                "text": item["text"],
                "start": item["start"],
                "end": item["end"]
            })

    # Date range detection
    if (
        len(dates) >= 2
        and re.search(r"\bbetween\b", question, re.IGNORECASE)
        and re.search(r"\band\b", question, re.IGNORECASE)
    ):

        start_date = dates[0]["date"]
        end_date = dates[1]["date"]

        # Inherit year from the second date if first date has no year.
        if not re.search(r"\b\d{4}\b", dates[0]["text"]):
            start_date = start_date.replace(year=end_date.year)

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date.")

        return {
            "type": "date_range",
            "start_date": start_date,
            "end_date": end_date
        }

    # Exact date
    if dates:
        return {
            "type": "exact_date",
            "value": dates[0]["date"]
        }

    return None



def extract_grouping(question, metric_key):

    if metric_key not in METRICS:
        raise ValueError(f"Unapproved metric: {metric_key}")

    question_lower = question.lower()

    allowed_columns = load_dimensions()
    selected_dimensions = []

    for key, config in DIMENSION_MAP.items():

        if not config.get("groupable", False):
            continue

        synonyms = config.get("synonyms", []) + [key]

        for synonym in synonyms:

            synonym = synonym.lower().strip()

            # Match the first dimension after "by"
            # and additional dimensions after "and" or comma.
            patterns = [
                r"(?:\bby\s+|\band\s+|,\s*)"
                + re.escape(synonym)
                + r"\b",

                # Support "district wise", "base location wise", etc.
                r"\b" + re.escape(synonym) + r"\s+wise\b"
            ]

            # Daily/monthly/yearly grouping
            if synonym in ["daily", "monthly", "yearly"]:
                patterns.append(
                    r"\b" + re.escape(synonym) + r"\b"
                )

            if any(
                re.search(pattern, question_lower)
                for pattern in patterns
            ):

                reference = config["reference"]

                if (
                    reference in allowed_columns
                    and reference not in selected_dimensions
                ):
                    selected_dimensions.append(reference)

                break

    return {
        "metric": metric_key,
        "group_by": selected_dimensions,
        "date_filter": extract_date_filter(question)
    }
