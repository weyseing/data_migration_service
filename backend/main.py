from fastapi import FastAPI, HTTPException

from backend.config import get_source_engine
from backend.discovery import run_discovery
from backend.discovery.graph import build_dependency_graph, export_dot, get_load_order
from backend.models.discovery import DiscoveryResult

app = FastAPI(title="Mini IronBook", version="0.1.0")

_discovery_cache: DiscoveryResult | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/discovery/run")
def api_run_discovery():
    global _discovery_cache
    engine = get_source_engine()
    _discovery_cache = run_discovery(engine)
    return _discovery_cache


@app.get("/api/discovery/tables")
def api_tables():
    if not _discovery_cache:
        raise HTTPException(404, "Run discovery first")
    return _discovery_cache.tables


@app.get("/api/discovery/tables/{name}")
def api_table(name: str):
    if not _discovery_cache:
        raise HTTPException(404, "Run discovery first")
    for t in _discovery_cache.tables:
        if t.name == name:
            return t
    raise HTTPException(404, f"Table '{name}' not found")


@app.get("/api/discovery/procedures")
def api_procedures():
    if not _discovery_cache:
        raise HTTPException(404, "Run discovery first")
    return _discovery_cache.stored_procedures


@app.get("/api/discovery/graph")
def api_graph():
    if not _discovery_cache:
        raise HTTPException(404, "Run discovery first")
    graph = build_dependency_graph(_discovery_cache.tables)
    return {
        "edges": _discovery_cache.dependency_edges,
        "load_order": get_load_order(graph),
        "dot": export_dot(graph),
    }
