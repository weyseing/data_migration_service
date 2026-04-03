from sqlalchemy.engine import Engine

from backend.config import get_source_schema
from backend.discovery.graph import build_dependency_graph
from backend.discovery.scanner import scan_tables
from backend.discovery.sql_parser import (
    extract_stored_procedures,
    extract_triggers,
    extract_views,
)
from backend.models.discovery import DiscoveryResult


def run_discovery(engine: Engine) -> DiscoveryResult:
    schema = get_source_schema()
    tables = scan_tables(engine)
    procs = extract_stored_procedures(engine, schema)
    views = extract_views(engine, schema)
    triggers = extract_triggers(engine, schema)
    graph = build_dependency_graph(tables)

    return DiscoveryResult(
        tables=tables,
        stored_procedures=procs,
        views=views,
        triggers=triggers,
        dependency_edges=list(graph.edges()),
    )
