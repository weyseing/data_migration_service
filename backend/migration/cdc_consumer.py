import base64
import json
import struct
from datetime import datetime, timezone
from decimal import Decimal

from kafka import KafkaConsumer
from sqlalchemy import text

from backend.config import KAFKA_BROKER, get_target_engine
from backend.models.discovery import DiscoveryResult

# Debezium sends timestamps as epoch millis — these source types need conversion
_TIMESTAMP_TYPES = {"DATETIME", "TIMESTAMP", "DATE"}
_DECIMAL_TYPES = {"DECIMAL", "NUMERIC"}


def _decode_debezium_decimal(val: str, scale: int) -> Decimal:
    """Decode Debezium's base64-encoded big-endian two's-complement decimal."""
    raw = base64.b64decode(val)
    # Big-endian two's complement integer
    unscaled = int.from_bytes(raw, byteorder="big", signed=True)
    return Decimal(unscaled) / (Decimal(10) ** scale)


def _get_decimal_scale(data_type: str) -> int:
    """Extract scale from type like DECIMAL(12,2) → 2."""
    if "," in data_type:
        return int(data_type.split(",")[1].strip().rstrip(")"))
    return 0


def _convert_debezium_values(after: dict, columns: list, type_map: dict) -> dict:
    """Convert Debezium-encoded values to Python types."""
    result = {}
    for col in columns:
        if col not in after:
            continue
        val = after[col]
        src_type = type_map.get(col, "").upper()

        if val is not None and src_type in _TIMESTAMP_TYPES and isinstance(val, (int, float)):
            result[col] = datetime.fromtimestamp(val / 1000, tz=timezone.utc).replace(tzinfo=None)
        elif val is not None and isinstance(val, str) and any(src_type.startswith(t) for t in _DECIMAL_TYPES):
            scale = _get_decimal_scale(type_map.get(col, ""))
            result[col] = _decode_debezium_decimal(val, scale)
        else:
            result[col] = val
    return result


def replay_cdc(discovery: DiscoveryResult, timeout_ms: int = 5000) -> int:
    """Consume Debezium CDC events from Kafka and apply UPSERT/DELETE on target.

    Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE) to safely handle overlap
    between the full load and CDC events.

    Returns the number of events applied.
    """
    table_names = [t.name for t in discovery.tables]
    topics = [f"source.source_db.{name}" for name in table_names]

    # Map table name → primary key columns
    pk_map = {t.name: t.primary_key for t in discovery.tables}
    # Map table name → all column names
    col_map = {t.name: [c.name for c in t.columns] for t in discovery.tables}
    # Map table name → {column_name: source_data_type} for timestamp conversion
    type_map = {t.name: {c.name: c.data_type for c in t.columns} for t in discovery.tables}

    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        group_id="ironbook-cdc-replay",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        consumer_timeout_ms=timeout_ms,
    )

    engine = get_target_engine()
    events_applied = 0

    try:
        with engine.connect() as conn:
            for message in consumer:
                if not message.value:
                    continue

                payload = message.value.get("payload")
                if not payload:
                    continue

                op = payload.get("op")  # c=create, u=update, d=delete, r=read(snapshot)
                # Extract table name from topic: source.source_db.table_name
                table_name = message.topic.split(".")[-1]
                pk_cols = pk_map.get(table_name, [])
                all_cols = col_map.get(table_name, [])

                if not pk_cols or not all_cols:
                    continue

                if op in ("c", "u", "r"):
                    # UPSERT: INSERT ... ON CONFLICT (pk) DO UPDATE
                    after = payload.get("after", {})
                    if not after:
                        continue

                    vals = _convert_debezium_values(after, all_cols, type_map.get(table_name, {}))
                    cols = list(vals.keys())
                    placeholders = ", ".join(f":{c}" for c in cols)
                    col_list = ", ".join(cols)
                    update_cols = [c for c in cols if c not in pk_cols]
                    update_set = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

                    if update_set:
                        sql = (
                            f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
                            f"ON CONFLICT ({', '.join(pk_cols)}) DO UPDATE SET {update_set}"
                        )
                    else:
                        sql = (
                            f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
                            f"ON CONFLICT ({', '.join(pk_cols)}) DO NOTHING"
                        )

                    conn.execute(text(sql), vals)
                    conn.commit()
                    events_applied += 1

                elif op == "d":
                    # DELETE
                    before = payload.get("before", {})
                    if not before:
                        continue

                    where = " AND ".join(f"{c} = :{c}" for c in pk_cols)
                    vals = {c: before[c] for c in pk_cols}
                    conn.execute(text(f"DELETE FROM {table_name} WHERE {where}"), vals)
                    conn.commit()
                    events_applied += 1

    finally:
        consumer.close()

    return events_applied
