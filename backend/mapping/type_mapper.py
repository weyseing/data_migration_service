import re

import sqlglot
from sqlglot import exp

from backend.models.discovery import ColumnInfo, TableInfo
from backend.models.mapping import ColumnMapping, TableMapping


def map_column_type(col: ColumnInfo) -> ColumnMapping:
    """Map a single MySQL column type to PostgreSQL using SQLGlot."""
    source_type = col.data_type
    notes = ""

    # Handle ENUM specially — SQLGlot doesn't transpile ENUM values
    enum_match = re.match(r"ENUM\((.+)\)", source_type, re.IGNORECASE)
    if enum_match:
        values = enum_match.group(1)
        target_type = f"TEXT CHECK ({col.name} IN ({values}))"
        notes = "MySQL ENUM mapped to TEXT with CHECK constraint"
        return ColumnMapping(
            source_column=col.name,
            source_type=source_type,
            target_type=target_type,
            notes=notes,
        )

    # Handle UNSIGNED — strip it, add note
    clean_type = source_type
    if "UNSIGNED" in source_type.upper():
        clean_type = re.sub(r"\s*UNSIGNED", "", source_type, flags=re.IGNORECASE).strip()
        notes = "UNSIGNED removed (PostgreSQL does not support unsigned integers)"

    # Use SQLGlot to transpile the type
    try:
        # Wrap in a CREATE TABLE to let SQLGlot parse and transpile
        create_sql = f"CREATE TABLE _t ({col.name} {clean_type})"
        transpiled = sqlglot.transpile(create_sql, read="mysql", write="postgres")[0]
        # Extract the type from the transpiled CREATE TABLE
        parsed = sqlglot.parse_one(transpiled, dialect="postgres")
        col_def = parsed.find(exp.ColumnDef)
        if col_def:
            target_type = col_def.args["kind"].sql(dialect="postgres")
        else:
            target_type = clean_type
    except Exception:
        # Fallback: return as-is
        target_type = clean_type
        if not notes:
            notes = "Could not transpile, kept original type"

    return ColumnMapping(
        source_column=col.name,
        source_type=source_type,
        target_type=target_type,
        notes=notes,
    )


def map_table(table: TableInfo) -> TableMapping:
    """Map all columns in a table from MySQL to PostgreSQL types."""
    return TableMapping(
        source_table=table.name,
        column_mappings=[map_column_type(col) for col in table.columns],
    )


def map_all_tables(tables: list[TableInfo]) -> list[TableMapping]:
    """Map all tables."""
    return [map_table(t) for t in tables]
