from pydantic import BaseModel


class TableDDL(BaseModel):
    table_name: str
    ddl: str
    valid: bool = False
    error: str = ""


class ProcedureRefactor(BaseModel):
    source_name: str
    source_body: str
    target_sql: str
    explanation: str = ""
    valid: bool = False
    error: str = ""


class RefactoringResult(BaseModel):
    table_ddls: list[TableDDL]
    procedure_refactors: list[ProcedureRefactor]
