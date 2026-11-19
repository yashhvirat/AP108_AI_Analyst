from backend.dimension_map import DIMENSION_MAP
from backend.dax_executor import execute_dax

# In-memory cache
DIMENSION_CACHE = {}


def load_dimension_values(force_refresh=False):

    global DIMENSION_CACHE

    if DIMENSION_CACHE and not force_refresh:
        return DIMENSION_CACHE

    new_cache = {}

    for key, config in DIMENSION_MAP.items():

        if not config["filterable"]:
            continue

        reference = config["reference"]

        dax = f"""
        EVALUATE
        FILTER(
            DISTINCT(
                {reference}
            ),
            NOT ISBLANK({reference})
        )
        """

        try:
            result = execute_dax(dax)

            # execute_dax() returns a Pandas DataFrame
            if hasattr(result, "iloc"):
                values = result.iloc[:, 0].dropna().tolist()
            else:
                values = []
                for row in result:
                    if isinstance(row, (list, tuple)):
                        value = row[0]
                    elif isinstance(row, dict):
                        value = next(iter(row.values()), None)
                    else:
                        value = row

                    if value is not None:
                        values.append(value)

            new_cache[key] = values

            # print(
            #     f"Loaded {len(values)} values "
            #     f"for {key}"
            # )

        except Exception as e:

            print(f"Failed loading {key}: {e}")
            raise

    DIMENSION_CACHE = new_cache

    return DIMENSION_CACHE


def validate_dimension_value(dimension, requested_value):

    cache = load_dimension_values()

    if dimension not in cache:
        return {
            "valid": False,
            "matched_value": None
        }

    requested = str(requested_value).strip().casefold()

    for actual_value in cache[dimension]:

        if str(actual_value).strip().casefold() == requested:

            return {
                "valid": True,
                "matched_value": actual_value
            }

    return {
        "valid": False,
        "matched_value": None
    }
