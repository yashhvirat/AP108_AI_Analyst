
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "knowledge"
KNOWLEDGE.mkdir(exist_ok=True)

# Load metadata
tables = pd.read_csv(ROOT / "tables.csv")
columns = pd.read_csv(ROOT / "columns.csv")
measures = pd.read_csv(ROOT / "measures.csv")
relationships = pd.read_csv(ROOT / "relationships.csv")

# Map TableID to actual table names
table_map = dict(zip(tables["ID"], tables["Name"]))

columns["TableName"] = columns["TableID"].map(table_map)
measures["TableName"] = measures["TableID"].map(table_map)

lines = []

lines.append("# POWER BI SEMANTIC MODEL SCHEMA")
lines.append("")

# Tables, columns and measures
for _, table in tables.iterrows():

    table_id = table["ID"]
    table_name = table["Name"]

    lines.append(f"## TABLE: {table_name}")
    lines.append("")

    # Columns
    table_columns = columns[columns["TableID"] == table_id]

    lines.append("### Columns")

    for _, col in table_columns.iterrows():

        lines.append(
            f'- {col["ExplicitName"]} '
            f'(Data type: {col["ExplicitDataType"]}, '
            f'Hidden: {col["IsHidden"]})'
        )

    lines.append("")

    # Measures
    table_measures = measures[measures["TableID"] == table_id]

    lines.append("### Measures")

    for _, measure in table_measures.iterrows():

        lines.append(
            f'- {measure["Name"]}: '
            f'{measure["Expression"]}'
        )

    lines.append("")
    lines.append("---")
    lines.append("")

# Relationships
lines.append("# MODEL RELATIONSHIPS")
lines.append("")

for _, rel in relationships.iterrows():

    from_table = table_map.get(rel["FromTableID"], "Unknown")
    to_table = table_map.get(rel["ToTableID"], "Unknown")

    from_col = columns.loc[
        columns["ID"] == rel["FromColumnID"], "ExplicitName"
    ]

    to_col = columns.loc[
        columns["ID"] == rel["ToColumnID"], "ExplicitName"
    ]

    from_column = from_col.iloc[0] if not from_col.empty else "Unknown"
    to_column = to_col.iloc[0] if not to_col.empty else "Unknown"

    active = rel["IsActive"]

    lines.append(
        f"- {from_table}[{from_column}] -> "
        f"{to_table}[{to_column}] "
        f"(Active: {active}, "
        f"Cross filtering: {rel['CrossFilteringBehavior']})"
    )

# Save schema
schema_text = "\n".join(lines)

output_file = KNOWLEDGE / "schema_context.md"
output_file.write_text(schema_text, encoding="utf-8")

print("Schema generated successfully!")
print("Output:", output_file)
print("Tables:", len(tables))
print("Columns:", len(columns))
print("Measures:", len(measures))
print("Relationships:", len(relationships))