import json

import httpx

from backend.config import DEBEZIUM_URL

CONNECTOR_NAME = "source-mysql-connector"


def start_cdc() -> bool:
    """Register the Debezium MySQL connector. Returns True if started successfully."""
    connector_config = {
        "name": CONNECTOR_NAME,
        "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "database.hostname": "mysql",
            "database.port": "3306",
            "database.user": "migration",
            "database.password": "migration123",
            "database.server.id": "1",
            "topic.prefix": "source",
            "database.include.list": "source_db",
            "schema.history.internal.kafka.bootstrap.servers": "redpanda:29092",
            "schema.history.internal.kafka.topic": "schema-changes",
            "snapshot.mode": "never",
        },
    }

    # Delete existing connector if present (clean state)
    httpx.delete(f"{DEBEZIUM_URL}/connectors/{CONNECTOR_NAME}")

    resp = httpx.post(
        f"{DEBEZIUM_URL}/connectors",
        headers={"Content-Type": "application/json"},
        content=json.dumps(connector_config),
    )
    return resp.status_code in (200, 201)


def stop_cdc() -> bool:
    """Delete the Debezium connector."""
    resp = httpx.delete(f"{DEBEZIUM_URL}/connectors/{CONNECTOR_NAME}")
    return resp.status_code in (200, 204)


def get_cdc_status() -> dict:
    """Get connector status."""
    try:
        resp = httpx.get(f"{DEBEZIUM_URL}/connectors/{CONNECTOR_NAME}/status")
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}
