import io
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import text

from backend.config import get_source_engine, get_target_engine
from backend.discovery.graph import build_dependency_graph, get_load_order
from backend.models.discovery import DiscoveryResult, TableInfo
from backend.models.migration import TableLoadResult

BATCH_SIZE = 5000
MAX_WORKERS = 4


def _load_table(table: TableInfo) -> TableLoadResult:
    """Bulk load a single table from MySQL to PostgreSQL using batched COPY."""
    src_engine = get_source_engine()
    tgt_engine = get_target_engine()

    col_names = [c.name for c in table.columns]
    cols_csv = ", ".join(col_names)

    total_rows = 0
    try:
        with src_engine.connect() as src_conn:
            rows = src_conn.execute(text(f"SELECT {cols_csv} FROM {table.name}")).fetchall()

        with tgt_engine.connect() as tgt_conn:
            raw_conn = tgt_conn.connection.dbapi_connection
            cursor = raw_conn.cursor()

            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                buf = io.StringIO()
                for row in batch:
                    line = "\t".join(
                        "\\N" if v is None else str(v) for v in row
                    )
                    buf.write(line + "\n")
                buf.seek(0)
                cursor.copy_expert(
                    f"COPY {table.name} ({cols_csv}) FROM STDIN WITH (FORMAT text)",
                    buf,
                )
                total_rows += len(batch)

            raw_conn.commit()

        return TableLoadResult(
            table_name=table.name, rows_copied=total_rows, success=True
        )
    except Exception as e:
        return TableLoadResult(
            table_name=table.name,
            rows_copied=total_rows,
            success=False,
            error=str(e).split("\n")[0],
        )


def bulk_load_all(discovery: DiscoveryResult) -> list[TableLoadResult]:
    """Load all tables in dependency order, parallelising independent tables."""
    graph = build_dependency_graph(discovery.tables)
    load_order = get_load_order(graph)
    table_by_name = {t.name: t for t in discovery.tables}

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        loaded = set()
        remaining = list(load_order)

        while remaining:
            # Find tables whose FK dependencies are all loaded
            ready = [
                name
                for name in remaining
                if all(dep in loaded for dep in graph.successors(name))
            ]
            if not ready:
                break

            futures = {}
            for name in ready:
                table = table_by_name.get(name)
                if table:
                    futures[pool.submit(_load_table, table)] = name

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                loaded.add(futures[future])

            for name in ready:
                remaining.remove(name)

    return results
