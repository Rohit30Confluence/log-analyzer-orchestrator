"""SQLite-backed persistence for approval requests. Boring on purpose."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

from orchestrator.models.approval import ApprovalRequest, ApprovalStatus

# Respects DB_PATH env var so deploy configs can point this at a mounted
# persistent disk (e.g. Render's /app/data) instead of the container's
# ephemeral filesystem. Falls back to a local file for dev.
DEFAULT_DB_PATH = Path(os.environ.get("DB_PATH", "approvals.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals (status);
CREATE INDEX IF NOT EXISTS idx_approvals_event_id ON approvals (event_id);
"""


class Repository:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def save(self, approval: ApprovalRequest) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO approvals (approval_id, event_id, status, data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(approval_id) DO UPDATE SET
                    status = excluded.status,
                    data = excluded.data
                """,
                (
                    approval.approval_id,
                    approval.event_id,
                    approval.status,
                    approval.model_dump_json(),
                ),
            )

    def get(self, approval_id: str) -> Optional[ApprovalRequest]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM approvals WHERE approval_id = ?", (approval_id,)
            ).fetchone()
        if row is None:
            return None
        return ApprovalRequest.model_validate_json(row["data"])

    def list(self, status: Optional[ApprovalStatus] = None, limit: int = 100) -> list[ApprovalRequest]:
        with self._connect() as conn:
            if status is not None:
                rows = conn.execute(
                    "SELECT data FROM approvals WHERE status = ? ORDER BY rowid DESC LIMIT ?",
                    (status.value if isinstance(status, ApprovalStatus) else status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM approvals ORDER BY rowid DESC LIMIT ?", (limit,)
                ).fetchall()
        return [ApprovalRequest.model_validate_json(r["data"]) for r in rows]
