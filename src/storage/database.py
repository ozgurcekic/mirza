# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DB_DIR = os.path.expanduser("~/.local/share/mirza")
DB_PATH = os.path.join(DB_DIR, "activity.db")

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS focus_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    process_name TEXT NOT NULL,
    window_title TEXT,
    window_geometry TEXT,
    workspace INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS usage_durations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_name TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS driver_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    process_name TEXT,
    subsystem TEXT NOT NULL,
    action TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS system_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    cpu_percent REAL,
    ram_percent REAL,
    gpu_percent REAL,
    disk_mb_s REAL,
    net_mb_s REAL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    tags TEXT
);

CREATE TABLE IF NOT EXISTS transition_counts (
    from_app TEXT NOT NULL,
    to_app TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    time_bucket INTEGER,
    PRIMARY KEY (from_app, to_app, time_bucket)
);

CREATE INDEX IF NOT EXISTS idx_focus_timestamp ON focus_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_focus_process ON focus_events(process_name);
CREATE INDEX IF NOT EXISTS idx_durations_process ON usage_durations(process_name);
CREATE INDEX IF NOT EXISTS idx_transitions_from ON transition_counts(from_app);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON system_snapshots(timestamp);
"""


class Database:
    def __init__(self, db_path=DB_PATH):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()
        logger.info("Database initialized at %s", db_path)

    def _init_schema(self):
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def execute(self, query, params=None):
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)
        self.conn.commit()
        return cursor

    def fetch_all(self, query, params=None):
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)
        return cursor.fetchall()

    def fetch_one(self, query, params=None):
        if params:
            cursor = self.conn.execute(query, params)
        else:
            cursor = self.conn.execute(query)
        return cursor.fetchone()

    def cleanup_old_data(self, days=90):
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        tables = ["focus_events", "usage_durations", "driver_events",
                  "system_snapshots"]
        for table in tables:
            self.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))
        logger.info("Cleaned up data older than %d days", days)

    def close(self):
        self.conn.close()
        logger.info("Database connection closed")
