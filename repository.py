"""
SQLite-backed persistence. Deliberately boring: no ORM, just sqlite3 +
JSON blobs keyed by id. Swap for Postgres later if/when concurrency
actually demands it — premature to build that now.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from orchestrator.models.event import EventRecord
from orchestrator.models.workflow import Workflow

DEFAULT_DB_PATH = Path("orchestrator.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    correlation_id TEXT,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events (event_id)
);

CREATE INDEX IF NOT EXISTS idx_workflows_event_id ON workflows (event_id);
"""


class Repository:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ---- events ----

    def save_event(self, event: EventRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (event_id, correlation_id, data) VALUES (?, ?, ?)",
                (event.event_id, event.correlation_id, event.model_dump_json()),
            )

    def get_event(self, event_id: str) -> Optional[EventRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
        if row is None:
            return None
        return EventRecord.model_validate_json(row["data"])

    def list_events(self, limit: int = 50) -> list[EventRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM events ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return [EventRecord.model_validate_json(r["data"]) for r in rows]

    # ---- workflows ----

    def save_workflow(self, workflow: Workflow) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflows (workflow_id, event_id, status, data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workflow_id) DO UPDATE SET
                    status = excluded.status,
                    data = excluded.data
                """,
                (
                    workflow.workflow_id,
                    workflow.event_id,
                    workflow.status,
                    workflow.model_dump_json(),
                ),
            )

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
        if row is None:
            return None
        return Workflow.model_validate_json(row["data"])

    def get_workflow_for_event(self, event_id: str) -> Optional[Workflow]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM workflows WHERE event_id = ? ORDER BY rowid DESC LIMIT 1",
                (event_id,),
            ).fetchone()
        if row is None:
            return None
        return Workflow.model_validate_json(row["data"])
