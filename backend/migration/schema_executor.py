from sqlalchemy import text

from backend.config import get_target_engine
from backend.discovery.graph import build_dependency_graph, get_load_order
from backend.models.discovery import DiscoveryResult
from backend.models.refactoring import RefactoringResult


def execute_schema(
    refactoring: RefactoringResult,
    discovery: DiscoveryResult,
) -> list[str]:
    """Execute CREATE TABLE DDL on target PostgreSQL. Returns list of errors (empty = success)."""
    graph = build_dependency_graph(discovery.tables)
    load_order = get_load_order(graph)
    ddl_by_name = {td.table_name: td for td in refactoring.table_ddls}

    errors = []
    engine = get_target_engine()

    with engine.connect() as conn:
        # Drop tables in reverse dependency order if they exist
        for name in reversed(load_order):
            conn.execute(text(f"DROP TABLE IF EXISTS {name} CASCADE"))
        conn.commit()

        # Create tables in dependency order
        for name in load_order:
            td = ddl_by_name.get(name)
            if not td:
                continue
            try:
                conn.execute(text(td.ddl))
                conn.commit()
            except Exception as e:
                errors.append(f"{name}: {str(e).split(chr(10))[0]}")
                conn.rollback()

        # Create functions/procedures (drop first to handle return type changes)
        for proc in refactoring.procedure_refactors:
            try:
                conn.execute(text(f"DROP FUNCTION IF EXISTS {proc.source_name} CASCADE"))
                conn.commit()
                conn.execute(text(proc.target_sql))
                conn.commit()
            except Exception as e:
                errors.append(f"{proc.source_name}: {str(e).split(chr(10))[0]}")
                conn.rollback()

    return errors
