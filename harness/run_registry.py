from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    workflow     TEXT NOT NULL,
    subject      TEXT NOT NULL,
    status       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    started_at   TEXT,
    completed_at TEXT,
    attempt      INTEGER NOT NULL DEFAULT 1,
    inputs_json  TEXT NOT NULL,
    outputs_json TEXT,
    error        TEXT
)
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Run:
    run_id: str
    workflow: str
    subject: str
    status: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    attempt: int
    inputs: dict
    outputs: dict | None
    error: str | None


def _row_to_run(row: sqlite3.Row) -> Run:
    return Run(
        run_id=row["run_id"],
        workflow=row["workflow"],
        subject=row["subject"],
        status=row["status"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        attempt=row["attempt"],
        inputs=json.loads(row["inputs_json"]),
        outputs=json.loads(row["outputs_json"]) if row["outputs_json"] else None,
        error=row["error"],
    )


class RunRegistry:
    def __init__(self, db_path: str | Path) -> None:
        self._db = str(db_path)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def create_run(self, workflow: str, subject: str, inputs: dict) -> Run:
        run_id = str(uuid.uuid4())
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, workflow, subject, status, created_at, attempt, inputs_json) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (run_id, workflow, subject, PENDING, now, json.dumps(inputs)),
            )
        return Run(
            run_id=run_id,
            workflow=workflow,
            subject=subject,
            status=PENDING,
            created_at=now,
            started_at=None,
            completed_at=None,
            attempt=1,
            inputs=inputs,
            outputs=None,
            error=None,
        )

    def mark_running(self, run_id: str) -> None:
        now = _now()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT started_at FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            is_resume = row is not None and row["started_at"] is not None
            if is_resume:
                conn.execute(
                    "UPDATE runs SET status=?, started_at=?, attempt=attempt+1, error=NULL "
                    "WHERE run_id=?",
                    (RUNNING, now, run_id),
                )
            else:
                conn.execute(
                    "UPDATE runs SET status=?, started_at=? WHERE run_id=?",
                    (RUNNING, now, run_id),
                )

    def complete_run(self, run_id: str, outputs: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status=?, completed_at=?, outputs_json=? WHERE run_id=?",
                (COMPLETED, _now(), json.dumps(outputs), run_id),
            )

    def fail_run(self, run_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET status=?, completed_at=?, error=? WHERE run_id=?",
                (FAILED, _now(), error, run_id),
            )

    def get_run(self, run_id: str) -> Run | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id, workflow, subject, status, created_at, started_at, "
                "completed_at, attempt, inputs_json, outputs_json, error "
                "FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
        return _row_to_run(row) if row else None

    def list_runs(
        self,
        workflow: str | None = None,
        status: str | None = None,
    ) -> list[Run]:
        query = (
            "SELECT run_id, workflow, subject, status, created_at, started_at, "
            "completed_at, attempt, inputs_json, outputs_json, error FROM runs"
        )
        params: list = []
        clauses: list[str] = []
        if workflow:
            clauses.append("workflow = ?")
            params.append(workflow)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_run(r) for r in rows]
