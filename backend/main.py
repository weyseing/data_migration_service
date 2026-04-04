from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from backend.config import get_source_engine
from backend.discovery import run_discovery
from backend.discovery.graph import build_dependency_graph, export_dot, get_load_order
from backend.mapping import run_mapping
from backend.models.discovery import DiscoveryResult
from backend.models.mapping import MappingResult
from backend.models.migration import MigrationState
from backend.models.refactoring import RefactoringResult
from backend.migration import run_migration
from backend.refactoring import run_refactoring

app = FastAPI(title="Mini IronBook", version="0.1.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

_discovery_cache: DiscoveryResult | None = None
_mapping_cache: MappingResult | None = None
_refactoring_cache: RefactoringResult | None = None
_migration_cache: MigrationState | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return (FRONTEND_DIR / "index.html").read_text()


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


# --- Mapping endpoints ---


@app.post("/api/mapping/run")
def api_run_mapping():
    global _mapping_cache
    if not _discovery_cache:
        raise HTTPException(400, "Run discovery first")
    _mapping_cache = run_mapping(_discovery_cache)
    return _mapping_cache


@app.get("/api/mapping/tables")
def api_mapping_tables():
    if not _mapping_cache:
        raise HTTPException(404, "Run mapping first")
    return _mapping_cache.table_mappings


@app.get("/api/mapping/procedures")
def api_mapping_procedures():
    if not _mapping_cache:
        raise HTTPException(404, "Run mapping first")
    return _mapping_cache.procedure_mappings


# --- Refactoring endpoints ---


@app.post("/api/refactoring/run")
def api_run_refactoring():
    global _refactoring_cache
    if not _discovery_cache or not _mapping_cache:
        raise HTTPException(400, "Run discovery and mapping first")
    _refactoring_cache = run_refactoring(_discovery_cache, _mapping_cache)
    return _refactoring_cache


@app.get("/api/refactoring/ddl")
def api_refactoring_ddl():
    if not _refactoring_cache:
        raise HTTPException(404, "Run refactoring first")
    return _refactoring_cache.table_ddls


@app.get("/api/refactoring/procedures")
def api_refactoring_procedures():
    if not _refactoring_cache:
        raise HTTPException(404, "Run refactoring first")
    return _refactoring_cache.procedure_refactors


# --- Migration endpoints ---


@app.post("/api/migration/run")
def api_run_migration():
    global _migration_cache
    if not _discovery_cache or not _refactoring_cache:
        raise HTTPException(400, "Run discovery and refactoring first")
    _migration_cache = run_migration(_discovery_cache, _refactoring_cache)
    return _migration_cache


@app.get("/api/migration/status")
def api_migration_status():
    if not _migration_cache:
        raise HTTPException(404, "Run migration first")
    return _migration_cache
