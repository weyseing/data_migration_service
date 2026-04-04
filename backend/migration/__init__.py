from backend.models.discovery import DiscoveryResult
from backend.models.migration import MigrationPhase, MigrationState
from backend.models.refactoring import RefactoringResult
from backend.migration.bulk_loader import bulk_load_all
from backend.migration.cdc_consumer import replay_cdc
from backend.migration.cdc_manager import start_cdc, stop_cdc
from backend.migration.schema_executor import execute_schema
from backend.migration.validator import validate_migration


def run_migration(
    discovery: DiscoveryResult,
    refactoring: RefactoringResult,
) -> MigrationState:
    state = MigrationState()

    # Phase 1: Apply schema to target
    state.phase = MigrationPhase.SCHEMA
    errors = execute_schema(refactoring, discovery)
    state.schema_applied = len(errors) == 0
    state.schema_errors = errors
    if errors:
        state.phase = MigrationPhase.FAILED
        state.error = f"Schema failed: {len(errors)} error(s)"
        return state

    # Phase 2: Start CDC (capture changes during full load)
    state.phase = MigrationPhase.CDC_START
    state.cdc_started = start_cdc()
    if not state.cdc_started:
        state.phase = MigrationPhase.FAILED
        state.error = "Failed to start Debezium CDC connector"
        return state

    # Phase 3: Full load (bulk COPY all data)
    state.phase = MigrationPhase.FULL_LOAD
    state.table_loads = bulk_load_all(discovery)
    failed_loads = [t for t in state.table_loads if not t.success]
    if failed_loads:
        state.phase = MigrationPhase.FAILED
        state.error = f"Full load failed for: {', '.join(t.table_name for t in failed_loads)}"
        stop_cdc()
        return state

    # Phase 4: Replay CDC events (apply buffered changes with UPSERT)
    state.phase = MigrationPhase.CDC_REPLAY
    state.cdc_events_applied = replay_cdc(discovery)

    # Stop CDC
    stop_cdc()

    # Phase 5: Validate (row count + checksum)
    state.phase = MigrationPhase.VALIDATING
    state.validations = validate_migration(discovery)

    state.phase = MigrationPhase.COMPLETED
    return state
