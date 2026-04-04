import sqlglot

from backend.models.discovery import DiscoveryResult, TableInfo
from backend.models.mapping import TableMapping
from backend.models.refactoring import TableDDL


def _build_create_table(table: TableInfo, mapping: TableMapping) -> str:
    """Build a MySQL CREATE TABLE from discovery + mapped types, then transpile to PostgreSQL."""
    col_map = {cm.source_column: cm.target_type for cm in mapping.column_mappings}

    col_defs = []
    for col in table.columns:
        target_type = col_map.get(col.name, col.data_type)

        # CHECK constraints embedded in type (e.g. ENUM → TEXT CHECK(...))
        # need to be appended after the column definition, not as the type
        check_clause = ""
        if "CHECK" in target_type.upper():
            parts = target_type.split("CHECK", 1)
            target_type = parts[0].strip()
            check_clause = f" CHECK{parts[1]}"

        parts = [col.name, target_type]
        if not col.nullable:
            parts.append("NOT NULL")
        if col.default is not None:
            default_val = col.default
            # Strip MySQL-only ON UPDATE clause (PostgreSQL uses triggers instead)
            if "ON UPDATE" in default_val.upper():
                default_val = default_val[:default_val.upper().index("ON UPDATE")].strip()
            if default_val.upper() == "CURRENT_TIMESTAMP":
                default_val = "CURRENT_TIMESTAMP"
            if default_val:
                parts.append(f"DEFAULT {default_val}")
        if check_clause:
            parts.append(check_clause.strip())

        col_defs.append("  " + " ".join(parts))

    # Primary key constraint
    if table.primary_key:
        col_defs.append(f"  PRIMARY KEY ({', '.join(table.primary_key)})")

    # Foreign key constraints
    for fk in table.foreign_keys:
        src_cols = ", ".join(fk.constrained_columns)
        ref_cols = ", ".join(fk.referred_columns)
        col_defs.append(f"  FOREIGN KEY ({src_cols}) REFERENCES {fk.referred_table}({ref_cols})")

    ddl = f"CREATE TABLE {table.name} (\n"
    ddl += ",\n".join(col_defs)
    ddl += "\n);"

    return ddl


def generate_all_ddl(
    discovery: DiscoveryResult,
    table_mappings: list[TableMapping],
) -> list[TableDDL]:
    """Generate PostgreSQL CREATE TABLE DDL for all tables."""
    mapping_by_name = {tm.source_table: tm for tm in table_mappings}
    results = []

    for table in discovery.tables:
        mapping = mapping_by_name.get(table.name)
        if not mapping:
            continue
        ddl = _build_create_table(table, mapping)
        results.append(TableDDL(table_name=table.name, ddl=ddl))

    return results
