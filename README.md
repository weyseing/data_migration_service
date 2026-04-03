# Mini IronBook — AI-Powered Data Migration Service

Automates migrating databases from MySQL to PostgreSQL using AI-assisted schema discovery, type mapping, and stored procedure conversion.

![Dashboard](docs/screenshot_dashboard.png)

## Quick Start

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

docker compose up -d
# Open http://localhost:8000
```

## Pipeline

**Step 1: Discovery** — Scans source MySQL database using SQLAlchemy. Extracts tables, columns, types, foreign keys, stored procedures, and builds a dependency graph for safe migration order.

**Step 2: Mapping** — Maps MySQL types to PostgreSQL using SQLGlot (deterministic) and Claude Haiku (AI, for stored procedure conversion).

**Step 3: Refactoring** — *(coming soon)* Transpile DDL, rewrite procedures to modern SQL.

**Step 4: Migration** — *(coming soon)* Schema execution, CDC via Debezium, parallel bulk COPY, validation.

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Vue 3 (CDN) |
| Backend | FastAPI |
| AI | Claude Haiku |
| SQL Parsing | SQLGlot |
| DB Inspect | SQLAlchemy |
| CDC | Debezium + Redpanda |
| Infra | Docker Compose |

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/discovery/run` | Scan source database |
| GET | `/api/discovery/tables` | List discovered tables |
| GET | `/api/discovery/graph` | Dependency graph + load order |
| POST | `/api/mapping/run` | Run type + procedure mapping |
| GET | `/api/mapping/tables` | Type mapping results |
| GET | `/api/mapping/procedures` | AI procedure conversion results |
