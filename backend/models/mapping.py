from pydantic import BaseModel


class ColumnMapping(BaseModel):
    source_column: str
    source_type: str
    target_type: str
    notes: str = ""


class TableMapping(BaseModel):
    source_table: str
    column_mappings: list[ColumnMapping]


class ProcedureMapping(BaseModel):
    source_name: str
    source_body: str
    target_sql: str
    explanation: str = ""


class MappingResult(BaseModel):
    table_mappings: list[TableMapping]
    procedure_mappings: list[ProcedureMapping]
