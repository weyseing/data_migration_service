import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url


SOURCE_DB_URL = os.environ.get(
    "SOURCE_DB_URL", "mysql+pymysql://migration:migration123@localhost:3306/source_db"
)
TARGET_DB_URL = os.environ.get(
    "TARGET_DB_URL", "postgresql+psycopg2://migration:migration123@localhost:5432/target_db"
)
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:9092")
DEBEZIUM_URL = os.environ.get("DEBEZIUM_URL", "http://localhost:8083")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def get_source_engine() -> Engine:
    return create_engine(SOURCE_DB_URL, pool_pre_ping=True)


def get_target_engine() -> Engine:
    return create_engine(TARGET_DB_URL, pool_pre_ping=True)


def get_source_schema() -> str:
    return make_url(SOURCE_DB_URL).database
