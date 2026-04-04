import hashlib

from sqlalchemy import text

from backend.config import get_source_engine, get_target_engine
from backend.models.discovery import DiscoveryResult
from backend.models.migration import ValidationResult


def _checksum_table(engine, table_name: str, columns: list[str]) -> tuple[int, str]:
    """Get row count and a deterministic checksum for a table."""
    cols_csv = ", ".join(columns)
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        # Order by all columns for deterministic hash
        rows = conn.execute(
            text(f"SELECT {cols_csv} FROM {table_name} ORDER BY {cols_csv}")
        ).fetchall()

    hasher = hashlib.md5()
    for row in rows:
        hasher.update(str(tuple(row)).encode())

    return count, hasher.hexdigest()


def validate_migration(discovery: DiscoveryResult) -> list[ValidationResult]:
    """Compare row counts and checksums between source and target for all tables."""
    src_engine = get_source_engine()
    tgt_engine = get_target_engine()
    results = []

    for table in discovery.tables:
        col_names = [c.name for c in table.columns]
        try:
            src_count, src_hash = _checksum_table(src_engine, table.name, col_names)
            tgt_count, tgt_hash = _checksum_table(tgt_engine, table.name, col_names)
            results.append(
                ValidationResult(
                    table_name=table.name,
                    source_count=src_count,
                    target_count=tgt_count,
                    counts_match=src_count == tgt_count,
                    source_checksum=src_hash,
                    target_checksum=tgt_hash,
                    checksums_match=src_hash == tgt_hash,
                )
            )
        except Exception as e:
            results.append(
                ValidationResult(
                    table_name=table.name,
                    source_checksum=str(e).split("\n")[0],
                )
            )

    return results
