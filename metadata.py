import clr
from pathlib import Path
import pandas as pd

# 1. Load ADOMD.NET assembly FIRST
DLL_PATH = Path(
    r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\Microsoft.AnalysisServices.AdomdClient\v4.0_15.0.0.0__89845dcd8080cc91\Microsoft.AnalysisServices.AdomdClient.dll"
)

if not DLL_PATH.exists():
    raise FileNotFoundError(f"ADOMD.NET DLL not found: {DLL_PATH}")

clr.AddReference(str(DLL_PATH))

# 2. Import Pyadomd only after loading the assembly
from pyadomd import Pyadomd

PORT = "55189"

CONNECTION_STRING = (
    f"Provider=MSOLAP;"
    f"Data Source=localhost:{PORT};"
)


def execute_dmv(query):

    with Pyadomd(CONNECTION_STRING) as conn:
        with conn.cursor().execute(query) as cursor:

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=columns)


def get_tables():
    return execute_dmv("""
        SELECT [ID], [Name]
        FROM $SYSTEM.TMSCHEMA_TABLES
    """)


def get_columns():
    return execute_dmv("""
        SELECT
            [ID],
            [TableID],
            [ExplicitName],
            [ExplicitDataType],
            [Description],
            [IsHidden],
            [SourceColumn],
            [FormatString]
        FROM $SYSTEM.TMSCHEMA_COLUMNS
    """)


def get_measures():
    return execute_dmv("""
        SELECT
            [ID],
            [TableID],
            [Name],
            [Expression],
            [FormatString]
        FROM $SYSTEM.TMSCHEMA_MEASURES
    """)

def get_relationships():
    return execute_dmv("""
        SELECT
            [ID],
            [FromTableID],
            [FromColumnID],
            [ToTableID],
            [ToColumnID],
            [IsActive],
            [CrossFilteringBehavior],
            [FromCardinality],
            [ToCardinality]
        FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS
    """)


if __name__ == "__main__":

    print("Extracting Power BI metadata...")

    tables = get_tables()
    print("Get Tables Comleted...")

    columns = get_columns()
    print("Get Columns Comleted...")

    measures = get_measures()
    print("Get Measures Comleted...")

    relationships = get_relationships()
    print("Get Relationships Comleted...")

    tables.to_csv("tables.csv", index=False)
    columns.to_csv("columns.csv", index=False)
    measures.to_csv("measures.csv", index=False)
    relationships.to_csv("relationships.csv", index=False)

    print("Metadata extraction completed!")
    print("Tables:", len(tables))
    print("Columns:", len(columns))
    print("Measures:", len(measures))
    print("Relationships:", len(relationships))

    print("TABLES:", tables.columns.tolist())
    print("COLUMNS:", columns.columns.tolist())
    print("MEASURES:", measures.columns.tolist())
    print("RELATIONSHIPS:", relationships.columns.tolist())
