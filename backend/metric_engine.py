import re
from backend.aliases import ALIASES

BASE_FILTER = "'ERR'[Ambulance/Feeder vehicle] = \"Ambulance\", 'ERR'[Ambulance Base Location] <> \"Backup\""

import re

def normalize(text):
    text = str(text).lower()
    text = text.replace("%", " percent ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
    

def load_metrics():

    metrics = {}

    df = get_measures()

    for _, row in df.iterrows():

        measure_name = str(row["[Name]"]).strip()

        if not measure_name:
            continue

        metrics[measure_name] = {
            "synonyms": [normalize(measure_name)],
            "measure": measure_name,
            "display_name": measure_name,
            "type": "measure"
        }

    return metrics

METRICS = load_metrics()

for measure_name, aliases in ALIASES.items():

    if measure_name in METRICS:

        METRICS[measure_name]["synonyms"].extend(
            normalize(alias) for alias in aliases
        )

def identify_metric(question):

    question = normalize(question)

    matches = []

    for metric_key, metric in METRICS.items():

        for synonym in metric["synonyms"]:

            pattern = r"\b" + re.escape(synonym) + r"\b"

            if re.search(pattern, question):
                matches.append({
                    "length": len(synonym),
                    "measure": metric["measure"],
                    "display_name": metric["display_name"]
                })

    if not matches:
        return None

    matches.sort(key=lambda x: x["length"], reverse=True)

    return matches[0]


def build_dax(metric_key, date_filter=None, dimension_filters=None):
    """Build an executable DAX query for an approved metric."""
    if metric_key not in METRICS:
        raise ValueError(f"Unknown metric: {metric_key}")

    metric = METRICS[metric_key]

    if metric["type"] == "scalar":
        expression = metric["dax_expression"]

    elif metric["type"] == "measure":
        expression = f"[{metric['measure']}]"

    else:
        raise ValueError("Unsupported metric type")

    display_name = metric["display_name"]

    common_filters = build_common_filters(
        date_filter,
        dimension_filters
    )

    dax = f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "{metric['display_name']}",
            {expression}
        ),
        {common_filters}
    )
    """

    return dax.strip()



def build_grouped_dax(
    metric_key,
    group_by,
    allowed_columns,
    date_filter=None,
    dimension_filters=None,
    ranking=None
):
    """
    Build grouped DAX with optional TOP N ranking.
    """

    if metric_key not in METRICS:
        raise ValueError(f"Unknown metric: {metric_key}")

    if not group_by:
        raise ValueError("At least one grouping column is required")

    for column in group_by:
        if column not in allowed_columns:
            raise ValueError(f"Unapproved column: {column}")

    metric = METRICS[metric_key]

    if metric["type"] == "scalar":
        expression = metric["dax_expression"]

    elif metric["type"] == "measure":
        expression = f"[{metric['measure']}]"

    else:
        raise ValueError("Unsupported metric type")

    group_columns = ",\n            ".join(group_by)

    common_filters = build_common_filters(
        date_filter,
        dimension_filters
    )

    summarize = f"""
        SUMMARIZECOLUMNS(
            {group_columns},
            "{metric['display_name']}",
            {expression}
        )
    """

    if ranking and ranking.get("enabled"):

        top_n = int(ranking["top_n"])
        order = ranking["order"]

        if top_n < 1:
            raise ValueError("top_n must be greater than zero")

        if order not in ("ASC", "DESC"):
            raise ValueError("Invalid ranking order")

        dax = f"""
        EVALUATE
        TOPN(
            {top_n},
            CALCULATETABLE(
                {summarize},
                {common_filters}
            ),
            [{metric['display_name']}],
            {order}
        )
        """

    else:

        dax = f"""
        EVALUATE
        CALCULATETABLE(
            {summarize},
            {common_filters}
        )
        """

    return dax.strip()




def build_common_filters(date_filter=None, dimension_filters=None):

    filters = [BASE_FILTER]

    # Exact date or date range
    if date_filter:

        date_type = date_filter.get("type")

        if date_type == "exact_date":

            value = date_filter["value"]

            filters.append(
                f"'Calender'[Date] = "
                f"DATE({value.year}, {value.month}, {value.day})"
            )

        elif date_type == "date_range":

            start_date = date_filter["start_date"]
            end_date = date_filter["end_date"]

            filters.append(
                "FILTER("
                "ALL('Calender'[Date]), "
                f"'Calender'[Date] >= DATE("
                f"{start_date.year}, {start_date.month}, {start_date.day}) "
                "&& "
                f"'Calender'[Date] <= DATE("
                f"{end_date.year}, {end_date.month}, {end_date.day})"
                ")"
            )

        else:
            raise ValueError(
                f"Unsupported date filter type: {date_type}"
            )

    # Dynamic dimension filters
    for item in dimension_filters or []:

        reference = item["reference"]
        values = item["values"]

        escaped_values = []

        for value in values:

            if isinstance(value, (int, float)):
                escaped_values.append(str(value))
            else:
                escaped_values.append(
                    '"' + str(value).replace('"', '""') + '"'
                )

        if len(escaped_values) == 1:

            filters.append(
                f"{reference} = {escaped_values[0]}"
            )

        else:

            filters.append(
                f"{reference} IN {{{', '.join(escaped_values)}}}"
            )

    return ",\n        ".join(filters)


