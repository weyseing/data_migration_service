# Mini IronBook — AI-Powered Data Migration Service

## What This Is
A mini version of IronBook AI's data migration platform. Automates migrating databases (MySQL/Oracle) to modern targets (PostgreSQL/Snowflake) using AI.

## Architecture

```
Streamlit Dashboard → FastAPI Backend → Source/Target DBs
                                     → Kafka (CDC)
                                     → Claude API (AI)
```

## Core Pipeline: 4 Steps

### Step 1: Discovery Engine
- SQLAlchemy inspects source DB: tables, columns, types, constraints, FKs
- Extract stored procedures, views, triggers
- Build dependency graph

### Step 2: Mapping Engine
- SQLGlot: deterministic type mapping (MySQL → PostgreSQL)
- Claude API: complex logic mapping (stored procs, business rules)

### Step 3: Refactoring Engine
- SQLGlot: transpile DDL across dialects
- Claude API: rewrite stored procedures to modern SQL
- Validate generated DDL against target DB

### Step 4: Migration Engine
- **Schema Execute**: run DDL on target
- **CDC Start**: Debezium reads binlog → Kafka (buffer changes)
- **Full Load**: parallel batched COPY (not row-by-row INSERT)
- **CDC Replay**: consume Kafka → UPSERT/DELETE on target (handles overlap)
- **Live Sync**: real-time streaming until cutover
- **Validate**: row count + checksum comparison

## Data Transfer Strategy

CDC alone does NOT cover historical data. The flow:
1. Start CDC (begin recording changes)
2. Full Load (bulk copy all old data, parallel threads)
3. CDC Replay (apply buffered changes using UPSERT to handle overlap)
4. Live Sync (real-time replication, seconds delay)
5. Validate + Cutover (switch traffic to new DB)

UPSERT on replay prevents duplicates when full load and CDC overlap.

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI | Claude API |
| SQL Parsing | SQLGlot |
| DB Inspect | SQLAlchemy |
| CDC | Debezium |
| Streaming | Redpanda (Kafka-compatible, no JVM) |
| State | SQLite |
| Infra | Docker Compose |

## Project Structure

```
mini-ironbook/
├── docker-compose.yml
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── discovery/    # scanner, sql_parser, graph
│   ├── mapping/      # type_mapper, ai_mapper
│   ├── refactoring/  # ddl_generator, transpiler, ai_refactor
│   ├── migration/    # schema_executor, bulk_loader, cdc_consumer, validator
│   └── models/       # schemas, state
├── frontend/
│   └── app.py
├── seed/             # sample MySQL schema + data
└── debezium/         # connector config
```

## Key Design Decisions

- Bulk COPY over row-by-row INSERT (10-50x faster)
- Redpanda over Kafka (single binary, no JVM, fast startup)
- SQLGlot for deterministic transforms, Claude API for complex logic
- UPSERT on CDC replay to handle full-load/CDC overlap safely
- Parallel batch workers for large table transfers
