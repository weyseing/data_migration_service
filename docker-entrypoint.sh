#!/bin/bash
set -e

echo "=== Mini IronBook - Starting ==="

# Wait for dependent services
echo "Waiting for MySQL..."
while ! python -c "
import pymysql
pymysql.connect(host='mysql', port=3306, user='migration', password='migration123', database='source_db')
" 2>/dev/null; do
    sleep 2
done
echo "MySQL ready."

echo "Waiting for PostgreSQL..."
while ! python -c "
import psycopg2
psycopg2.connect(host='postgres', port=5432, user='migration', password='migration123', dbname='target_db')
" 2>/dev/null; do
    sleep 2
done
echo "PostgreSQL ready."

echo "Waiting for Redpanda..."
while ! python -c "
from kafka import KafkaProducer
KafkaProducer(bootstrap_servers='redpanda:29092').close()
" 2>/dev/null; do
    sleep 2
done
echo "Redpanda ready."

# Start FastAPI backend (serves API + Vue frontend)
echo "Starting FastAPI on :8000"
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/backend
