from sqlalchemy import Enum as SAEnum, inspect as sa_inspect, text
from sqlalchemy.engine import Engine

from backend.models.discovery import ColumnInfo, ForeignKeyInfo, IndexInfo, TableInfo


def _type_to_str(col_type) -> str:
    if isinstance(col_type, SAEnum):
        values = ",".join(f"'{v}'" for v in col_type.enums)
        return f"ENUM({values})"
    return str(col_type)


def scan_tables(engine: Engine) -> list[TableInfo]:
    inspector = sa_inspect(engine)
    tables = []

    for table_name in inspector.get_table_names():
        # Columns
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = set(pk_constraint.get("constrained_columns", []))

        columns = []
        for col in inspector.get_columns(table_name):
            columns.append(ColumnInfo(
                name=col["name"],
                data_type=_type_to_str(col["type"]),
                nullable=col.get("nullable", True),
                default=str(col["default"]) if col.get("default") is not None else None,
                is_primary_key=col["name"] in pk_cols,
                autoincrement=col.get("autoincrement", False),
                comment=col.get("comment"),
            ))

        # Foreign keys
        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append(ForeignKeyInfo(
                constrained_columns=fk["constrained_columns"],
                referred_table=fk["referred_table"],
                referred_columns=fk["referred_columns"],
                name=fk.get("name"),
            ))

        # Indexes
        indexes = []
        for idx in inspector.get_indexes(table_name):
            indexes.append(IndexInfo(
                name=idx["name"],
                columns=idx["column_names"],
                unique=idx.get("unique", False),
            ))

        # Row count
        with engine.connect() as conn:
            row_count = conn.execute(
                text(f"SELECT COUNT(*) FROM `{table_name}`")
            ).scalar()

        tables.append(TableInfo(
            name=table_name,
            columns=columns,
            primary_key=list(pk_cols),
            foreign_keys=foreign_keys,
            indexes=indexes,
            row_count=row_count,
        ))

    return tables
