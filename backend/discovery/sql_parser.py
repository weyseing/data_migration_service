from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.models.discovery import StoredProcedure, TriggerInfo, ViewInfo


def extract_stored_procedures(engine: Engine, schema: str) -> list[StoredProcedure]:
    procs = []
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT ROUTINE_NAME, ROUTINE_DEFINITION "
            "FROM information_schema.ROUTINES "
            "WHERE ROUTINE_SCHEMA = :schema AND ROUTINE_TYPE = 'PROCEDURE'"
        ), {"schema": schema}).fetchall()

        for row in rows:
            name = row[0]
            # SHOW CREATE PROCEDURE gives full body reliably
            result = conn.execute(text(
                f"SHOW CREATE PROCEDURE `{schema}`.`{name}`"
            )).fetchone()
            body = (result[2] if result and result[2] else None) or row[1] or ""

            procs.append(StoredProcedure(
                name=name,
                body=body,
                param_list="",
                db=schema,
            ))
    return procs


def extract_views(engine: Engine, schema: str) -> list[ViewInfo]:
    views = []
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT TABLE_NAME, VIEW_DEFINITION "
            "FROM information_schema.VIEWS "
            "WHERE TABLE_SCHEMA = :schema"
        ), {"schema": schema}).fetchall()

        for row in rows:
            views.append(ViewInfo(name=row[0], definition=row[1] or ""))
    return views


def extract_triggers(engine: Engine, schema: str) -> list[TriggerInfo]:
    triggers = []
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT TRIGGER_NAME, EVENT_MANIPULATION, ACTION_TIMING, "
            "EVENT_OBJECT_TABLE, ACTION_STATEMENT "
            "FROM information_schema.TRIGGERS "
            "WHERE TRIGGER_SCHEMA = :schema"
        ), {"schema": schema}).fetchall()

        for row in rows:
            triggers.append(TriggerInfo(
                name=row[0],
                event=row[1],
                timing=row[2],
                table=row[3],
                body=row[4] or "",
            ))
    return triggers
