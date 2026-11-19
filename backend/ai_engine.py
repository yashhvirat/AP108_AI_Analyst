import re

from backend.metric_engine import (
    identify_metric,
    build_dax,
    build_grouped_dax
)

from backend.intent_engine import (
    extract_grouping,
    load_dimensions
)

from backend.filter_engine import extract_dimension_filters
from backend.dax_executor import execute_dax
from backend.ranking_engine import extract_ranking
from backend.dimension_map import DIMENSION_MAP


def ask_powerbi(question):

    try:

        # 1. Identify metric
        metric_info = identify_metric(question)

        if metric_info is None:
            raise ValueError("Metric not identified")

        metric_key = metric_info["measure"]

        # 2. Extract grouping and date
        intent = extract_grouping(
            question,
            metric_key
        )

        group_by = intent["group_by"]
        date_filter = intent["date_filter"]

        # 3. Extract dimension filters
        filter_result = extract_dimension_filters(
            question,
            date_filter=None
        )

        dimension_filters = filter_result["filters"]
        auto_group_by = filter_result["auto_group_by"]

        for column in auto_group_by:
            if column not in group_by:
                group_by.append(column)

        # 4. Extract ranking
        ranking = extract_ranking(question)

        # 5. Detect ranking dimension
        # 5. Detect ranking dimension dynamically
        if ranking["enabled"]:

            question_lower = question.lower()

            for dimension_key, config in DIMENSION_MAP.items():

                if not config.get("groupable", False):
                    continue

                aliases = config.get("synonyms", []) + [dimension_key]

                for alias in aliases:

                    pattern = (
                        r"\b"
                        + re.escape(alias.lower())
                        + r"s?\b"
                    )

                    if re.search(pattern, question_lower):

                        dimension_column = config["reference"]

                        if dimension_column not in group_by:
                            group_by.append(dimension_column)

                        break

        # 6. Generate DAX
        if group_by:

            dax = build_grouped_dax(
                metric_key,
                group_by,
                load_dimensions(),
                date_filter=date_filter,
                dimension_filters=dimension_filters,
                ranking=ranking
            )

        else:

            dax = build_dax(
                metric_key,
                date_filter=date_filter,
                dimension_filters=dimension_filters
            )

        # 7. Execute
        data = execute_dax(dax)

        return {
            "status": "success",
            "metric": metric_info,
            "intent": intent,
            "filters": dimension_filters,
            "ranking": ranking,
            "explanation": "Query executed successfully",
            "dax": dax,
            "data": data
        }

    except Exception as e:

        return {
            "status": "error",
            "metric": None,
            "intent": None,
            "filters": [],
            "ranking": None,
            "explanation": str(e),
            "dax": None,
            "data": None
        }
