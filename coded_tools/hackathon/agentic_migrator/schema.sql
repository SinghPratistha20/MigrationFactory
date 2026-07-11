-- coded_tools/hackathon/agentic_migrator/schema.sql
-- Reference PostgreSQL DDL. The project runs against a local SQLite file
-- (migration_runs.db, created automatically by db.py) by default; set
-- DATABASE_URL + install psycopg2-binary to point this at real Postgres
-- using the schema below instead.

CREATE TABLE IF NOT EXISTS migration_runs (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    run_id INT REFERENCES migration_runs(id),
    agent_name VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
