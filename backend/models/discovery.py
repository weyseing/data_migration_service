from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    default: str | None = None
    is_primary_key: bool = False
    autoincrement: bool = False
    comment: str | None = None


class ForeignKeyInfo(BaseModel):
    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]
    name: str | None = None


class IndexInfo(BaseModel):
    name: str
    columns: list[str]
    unique: bool


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    primary_key: list[str]
    foreign_keys: list[ForeignKeyInfo]
    indexes: list[IndexInfo]
    row_count: int | None = None


class StoredProcedure(BaseModel):
    name: str
    body: str
    param_list: str
    db: str


class ViewInfo(BaseModel):
    name: str
    definition: str


class TriggerInfo(BaseModel):
    name: str
    event: str
    timing: str
    table: str
    body: str


class DiscoveryResult(BaseModel):
    tables: list[TableInfo]
    stored_procedures: list[StoredProcedure]
    views: list[ViewInfo]
    triggers: list[TriggerInfo]
    dependency_edges: list[tuple[str, str]]
