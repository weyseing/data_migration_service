from enum import Enum

from pydantic import BaseModel


class MigrationPhase(str, Enum):
    PENDING = "pending"
    SCHEMA = "schema"
    CDC_START = "cdc_start"
    FULL_LOAD = "full_load"
    CDC_REPLAY = "cdc_replay"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class TableLoadResult(BaseModel):
    table_name: str
    rows_copied: int = 0
    success: bool = False
    error: str = ""


class ValidationResult(BaseModel):
    table_name: str
    source_count: int = 0
    target_count: int = 0
    counts_match: bool = False
    source_checksum: str = ""
    target_checksum: str = ""
    checksums_match: bool = False


class MigrationState(BaseModel):
    phase: MigrationPhase = MigrationPhase.PENDING
    schema_applied: bool = False
    schema_errors: list[str] = []
    cdc_started: bool = False
    table_loads: list[TableLoadResult] = []
    cdc_events_applied: int = 0
    validations: list[ValidationResult] = []
    error: str = ""
