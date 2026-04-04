from sqlalchemy import text

from backend.config import get_target_engine
from backend.discovery.graph import build_dependency_graph, get_load_order
from backend.models.discovery import DiscoveryResult
from backend.models.refactoring import ProcedureRefactor, TableDDL


def validate_all(
    table_ddls: list[TableDDL],
    procedure_refactors: list[ProcedureRefactor],
    discovery: DiscoveryResult,
) -> tuple[list[TableDDL], list[ProcedureRefactor]]:
    """Validate all DDLs and procedures in a single transaction.

    Tables are sorted by dependency order so FK references resolve.
    Each statement uses a savepoint so one failure doesn't poison the rest.
    """
    # Sort DDLs by dependency order (tables with no FKs first)
    graph = build_dependency_graph(discovery.tables)
    load_order = get_load_order(graph)
    ddl_by_name = {td.table_name: td for td in table_ddls}
    sorted_ddls = [ddl_by_name[name] for name in load_order if name in ddl_by_name]

    engine = get_target_engine()
    try:
        with engine.connect() as conn:
            txn = conn.begin()
            try:
                for td in sorted_ddls:
                    conn.execute(text(f"SAVEPOINT sp_{td.table_name}"))
                    try:
                        conn.execute(text(td.ddl))
                        td.valid = True
                        td.error = ""
                    except Exception as e:
                        td.valid = False
                        td.error = str(e).split("\n")[0]
                        conn.execute(text(f"ROLLBACK TO SAVEPOINT sp_{td.table_name}"))

                for proc in procedure_refactors:
                    conn.execute(text("SAVEPOINT sp_proc"))
                    try:
                        conn.execute(text(proc.target_sql))
                        proc.valid = True
                        proc.error = ""
                    except Exception as e:
                        proc.valid = False
                        proc.error = str(e).split("\n")[0]
                        conn.execute(text("ROLLBACK TO SAVEPOINT sp_proc"))
            finally:
                txn.rollback()
    except Exception as e:
        err = f"Connection failed: {e}"
        for td in sorted_ddls:
            td.valid = False
            td.error = err
        for proc in procedure_refactors:
            proc.valid = False
            proc.error = err

    return sorted_ddls, procedure_refactors
