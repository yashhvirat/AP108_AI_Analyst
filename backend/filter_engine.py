
import re
import calendar

from backend.dimension_map import DIMENSION_MAP
from backend.dimension_cache import load_dimension_values


def normalize(text):
    text = str(text).strip().lower()
    return re.sub(r"\s+", " ", text)


# Month aliases: abbreviated and full names
MONTH_ALIASES = {
    1: ["jan", "january"],
    2: ["feb", "february"],
    3: ["mar", "march"],
    4: ["apr", "april"],
    5: ["may"],
    6: ["jun", "june"],
    7: ["jul", "july"],
    8: ["aug", "august"],
    9: ["sep", "sept", "september"],
    10: ["oct", "october"],
    11: ["nov", "november"],
    12: ["dec", "december"]
}


def get_month_number(value):

    value = re.sub(r"[^a-z]", "", normalize(value))

    for month_number, aliases in MONTH_ALIASES.items():

        if value in aliases:
            return month_number

    return None


def extract_month_values(question, cached_values):

    question = normalize(question)

    matched_values = []

    for actual_value in cached_values:

        month_number = get_month_number(actual_value)

        if month_number is None:
            continue

        aliases = MONTH_ALIASES[month_number]

        for alias in aliases:

            # Match complete month words only.
            pattern = r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])"

            if re.search(pattern, question):

                if actual_value not in matched_values:
                    matched_values.append(actual_value)

                break

    return matched_values


def extract_dimension_filters(question, date_filter=None):

    question_lower = normalize(question)

    # Remove explicit date expressions before dimension matching.
    date_patterns = [
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\b",
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    if date_filter:
        for pattern in date_patterns:
            question_lower = re.sub(
                pattern,
                " ",
                question_lower,
                flags=re.IGNORECASE
            )

    cache = load_dimension_values()

    filters = []
    auto_group_by = []

    for key, config in DIMENSION_MAP.items():

        if not config["filterable"]:
            continue

        cached_values = cache.get(key, [])

        matched_values = []

        # Special handling for month names and abbreviations.
        if key == "month":

            matched_values = extract_month_values(
                question_lower,
                cached_values
            )

        else:

            # Existing dimension matching logic.
            sorted_values = sorted(
                cached_values,
                key=lambda x: len(str(x)),
                reverse=True
            )

            for actual_value in sorted_values:

                value = normalize(actual_value)

                if not value:
                    continue

                pattern = (
                    r"(?<![a-z0-9])"
                    + re.escape(value)
                    + r"(?![a-z0-9])"
                )

                if re.search(pattern, question_lower):

                    if actual_value not in matched_values:
                        matched_values.append(actual_value)

        if not matched_values:

            aliases = config.get("synonyms", []) + [key]

            for alias in aliases:

                if is_filter_context(question_lower, alias):

                    raise ValueError(
                        f"No matching {key.replace('_', ' ')} found "
                        f"for the requested value."
                    )

            continue

        # Handle multiple matched values
        if key == "month" and len(matched_values) > 1:

            # Group results separately by month
            auto_group_by.append(config["reference"])

            # Filter to only the requested months
            filters.append({
                "dimension": key,
                "reference": config["reference"],
                "values": matched_values
            })

        else:

            if len(matched_values) > 1:
                auto_group_by.append(config["reference"])

            filters.append({
                "dimension": key,
                "reference": config["reference"],
                "values": matched_values
            })

    return {
        "filters": filters,
        "auto_group_by": auto_group_by
    }


def is_filter_context(question, dimension_alias):

    question = normalize(question)
    alias = normalize(dimension_alias)

    match = re.search(
        r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])",
        question
    )

    if not match:
        return False

    before = question[:match.start()]

    # Filter-introducing words
    filter_words = ["in", "for", "at", "from", "within"]

    # Grouping-introducing words
    grouping_words = ["by", "and"]

    last_filter = max(
        [before.rfind(" " + word + " ") for word in filter_words],
        default=-1
    )

    last_grouping = max(
        [before.rfind(" " + word + " ") for word in grouping_words],
        default=-1
    )

    return last_filter > last_grouping