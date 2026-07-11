"""
coded_tools/hackathon/agentic_migrator/db.py
----------------------------------------------------------------
Lightweight persistence for migration runs and agent logs.
Uses a local SQLite file by default (zero setup). If DATABASE_URL
is set to a Postgres connection string and psycopg2 is installed,
it uses real Postgres instead (see schema.sql in this folder for
the equivalent DDL).
----------------------------------------------------------------
"""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "migration_runs.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

USE_POSTGRES = False
if DATABASE_URL:
    try:
        import psycopg2  # noqa: F401
        USE_POSTGRES = True
    except ImportError:
        USE_POSTGRES = False

_SCHEMA = """
CREATE TABLE IF NOT EXISTS migration_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, agent_name TEXT, message TEXT, created_at TEXT
);
"""


def get_connection():
    if USE_POSTGRES:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def new_run() -> int:
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    if USE_POSTGRES:
        cur.execute("INSERT INTO migration_runs (start_time, status) VALUES (%s, %s) RETURNING id", (now, "RUNNING"))
        run_id = cur.fetchone()[0]
    else:
        cur.execute("INSERT INTO migration_runs (start_time, status) VALUES (?, ?)", (now, "RUNNING"))
        run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id


def log_agent(run_id: int, agent_name: str, message: str):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    ph = "%s" if USE_POSTGRES else "?"
    cur.execute(f"INSERT INTO agent_logs (run_id, agent_name, message, created_at) VALUES ({ph},{ph},{ph},{ph})",
                (run_id, agent_name, message, now))
    conn.commit()
    conn.close()


def finish_run(run_id: int, status: str = "COMPLETED"):
    conn = get_connection()
    cur = conn.cursor()
    ph = "%s" if USE_POSTGRES else "?"
    cur.execute(f"UPDATE migration_runs SET status = {ph} WHERE id = {ph}", (status, run_id))
    conn.commit()
    conn.close()
