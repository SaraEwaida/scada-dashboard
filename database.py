"""
Historian Database
------------------
A lightweight SQLite-based historian for storing sensor readings.

In real SCADA systems, the historian is a time-series database that records
every process variable change so engineers can trend, audit, and diagnose
the plant. This module provides the same role on a small scale:

    - init_db()            : create the readings table on first run
    - log_reading(reading) : insert one sensor reading
    - log_all(readings)    : insert a batch of readings
    - get_history(tag, n)  : fetch the last n readings for a tag
    - get_active_alarms()  : fetch the latest reading per tag and flag alarms
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "historian.db"


@contextmanager
def get_conn():
    """Open a connection with row access by column name and ensure it closes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the readings table if it doesn't already exist."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tag       TEXT NOT NULL,
                name      TEXT NOT NULL,
                value     REAL NOT NULL,
                unit      TEXT NOT NULL,
                status    TEXT NOT NULL
            )
        """)
        # Index for fast "latest reading per tag" queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_tag_ts
            ON readings (tag, timestamp DESC)
        """)


def log_reading(reading):
    """Insert a single reading dict (as produced by sensor_simulator.read_sensor)."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO readings (timestamp, tag, name, value, unit, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (reading["timestamp"], reading["tag"], reading["name"],
             reading["value"], reading["unit"], reading["status"]),
        )


def log_all(readings):
    """Insert a list of readings in one transaction (faster than one by one)."""
    rows = [(r["timestamp"], r["tag"], r["name"], r["value"], r["unit"], r["status"])
            for r in readings]
    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO readings (timestamp, tag, name, value, unit, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )


def get_history(tag, limit=100):
    """Return the most recent `limit` readings for a tag, ordered oldest-first."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT timestamp, value, status FROM readings
               WHERE tag = ?
               ORDER BY id DESC LIMIT ?""",
            (tag, limit),
        ).fetchall()
    # Reverse so the newest reading is last (better for plotting)
    return [dict(r) for r in reversed(rows)]


def get_latest_per_tag():
    """Return the most recent reading for each tag (used for the dashboard cards)."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.tag, r.name, r.value, r.unit, r.status, r.timestamp
            FROM readings r
            INNER JOIN (
                SELECT tag, MAX(id) AS max_id FROM readings GROUP BY tag
            ) latest ON r.id = latest.max_id
            ORDER BY r.tag
        """).fetchall()
    return [dict(r) for r in rows]


def get_active_alarms():
    """Return the latest readings that are in WARNING or CRITICAL state."""
    return [r for r in get_latest_per_tag() if r["status"] != "NORMAL"]


def total_readings():
    """Count how many readings have been logged (for diagnostic display)."""
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]


# Self-test: run `python database.py` to verify it can store and retrieve data.
if __name__ == "__main__":
    from sensor_simulator import read_all

    print("Historian self-test\n" + "-" * 60)
    init_db()
    print("Database initialised.")

    print("Logging 10 batches of readings...")
    for _ in range(10):
        log_all(read_all())

    total = total_readings()
    print(f"Total readings stored: {total}")

    print("\nLatest reading per tag:")
    for r in get_latest_per_tag():
        print(f"  {r['tag']}  {r['name']:<22}  {r['value']:>8} {r['unit']:<5}"
              f"  [{r['status']}]")

    print("\nLast 5 history points for TT-101:")
    for r in get_history("TT-101", limit=5):
        print(f"  {r['timestamp']}  {r['value']}  [{r['status']}]")
