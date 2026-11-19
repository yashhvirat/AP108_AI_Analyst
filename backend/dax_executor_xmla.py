import os
import sys
import clr

# ADOMD.NET assembly location
ADOMD_PATH = r"C:\Program Files\Microsoft.NET\ADOMD.NET\170"

# Register DLL directory
sys.path.append(ADOMD_PATH)
os.environ["PATH"] = ADOMD_PATH + os.pathsep + os.environ["PATH"]

# Load ADOMD.NET assembly
clr.AddReference(
    os.path.join(ADOMD_PATH, "Microsoft.AnalysisServices.AdomdClient.dll")
)

import pandas as pd
from pyadomd import Pyadomd


# Power BI Service configuration
XMLA_ENDPOINT = r"powerbi://api.powerbi.com/v1.0/myorg/Bavya%20Analytics%20dashboards"
SEMANTIC_MODEL = "BHSPL AP 108 Operations Dashboard"

CONNECTION_STRING = (
    "Provider=MSOLAP;"
    f"Data Source={XMLA_ENDPOINT};"
    f"Initial Catalog={SEMANTIC_MODEL};"
)


def execute_dax(query):

    with Pyadomd(CONNECTION_STRING) as conn:

        with conn.cursor().execute(query) as cursor:

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


# if __name__ == "__main__":

#     query = """
#     EVALUATE
#     ROW(
#         "Connection Test", "Success",
#         "Dispatches", [Dispatches]
#     )
#     """

#     print(execute_dax(query))