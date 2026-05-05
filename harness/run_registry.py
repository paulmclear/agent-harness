from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

PENDING = "PENDING"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Base(DeclarativeBase):
    pass


class _RunRow(_Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    inputs_json: Mapped[str] = mapped_column(Text, nullable=False)
    outputs_json: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


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
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    error: str | None


def _row_to_run(row: _RunRow) -> Run:
    return Run(
        run_id=row.run_id,
        workflow=row.workflow,
        subject=row.subject,
        status=row.status,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        attempt=row.attempt,
        inputs=json.loads(row.inputs_json),
        outputs=json.loads(row.outputs_json) if row.outputs_json else None,
        error=row.error,
    )


class RunRegistry:
    def __init__(self, connection_url: str) -> None:
        kwargs: dict[str, Any] = {}
        if connection_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        self._engine = create_engine(connection_url, **kwargs)
        _Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def _session(self) -> Session:
        return self._Session()

    def create_run(self, workflow: str, subject: str, inputs: dict) -> Run:
        run_id = str(uuid.uuid4())
        now = _now()
        row = _RunRow(
            run_id=run_id,
            workflow=workflow,
            subject=subject,
            status=PENDING,
            created_at=now,
            attempt=1,
            inputs_json=json.dumps(inputs),
        )
        with self._session() as session:
            session.add(row)
            session.commit()
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
        with self._session() as session:
            row = session.get(_RunRow, run_id)
            if row is None:
                raise KeyError(f"Run not found: {run_id}")
            is_resume = row.started_at is not None
            row.status = RUNNING
            if is_resume:
                row.attempt += 1
                row.error = None
            else:
                row.started_at = now
            session.commit()

    def complete_run(self, run_id: str, outputs: dict) -> None:
        with self._session() as session:
            row = session.get(_RunRow, run_id)
            if row is None:
                raise KeyError(f"Run not found: {run_id}")
            row.status = COMPLETED
            row.completed_at = _now()
            row.outputs_json = json.dumps(outputs)
            session.commit()

    def fail_run(self, run_id: str, error: str) -> None:
        with self._session() as session:
            row = session.get(_RunRow, run_id)
            if row is None:
                raise KeyError(f"Run not found: {run_id}")
            row.status = FAILED
            row.completed_at = _now()
            row.error = error
            row.outputs_json = None
            session.commit()

    def get_run(self, run_id: str) -> Run | None:
        with self._session() as session:
            row = session.get(_RunRow, run_id)
            return _row_to_run(row) if row else None

    def list_runs(
        self,
        workflow: str | None = None,
        status: str | None = None,
    ) -> list[Run]:
        with self._session() as session:
            query = select(_RunRow)
            if workflow is not None:
                query = query.where(_RunRow.workflow == workflow)
            if status is not None:
                query = query.where(_RunRow.status == status)
            query = query.order_by(_RunRow.created_at.desc())
            rows = session.execute(query).scalars().all()
            return [_row_to_run(r) for r in rows]
