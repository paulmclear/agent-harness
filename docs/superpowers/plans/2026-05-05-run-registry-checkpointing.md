# Run Registry & Checkpointing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a general-purpose `harness/` package providing SQLite-backed run persistence and LangGraph checkpointing, then wire it into the `hubspot_company_research` workflow with `--resume` and `--list-runs` CLI support.

**Architecture:** `RunRegistry` (pure `sqlite3`) manages a `runs` table tracking lifecycle status, inputs, and outputs. `checkpoint.py` wraps LangGraph's `SqliteSaver`/`AsyncSqliteSaver` using the same DB file. The HubSpot workflow's `build_graph` accepts an injected checkpointer; a `run_workflow` helper wraps `graph.invoke` with status transitions.

**Tech Stack:** Python 3.11, LangGraph, `langgraph-checkpoint-sqlite`, `sqlite3` (stdlib), `uuid` (stdlib), `pytest`

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `harness/__init__.py` | Package marker |
| Create | `harness/run_registry.py` | `Run` dataclass, status constants, `RunRegistry` class |
| Create | `harness/checkpoint.py` | `make_sync_saver` and `make_async_saver` factories |
| Create | `harness/README.md` | User documentation |
| Create | `tests/__init__.py` | Test package marker |
| Create | `tests/harness/__init__.py` | Sub-package marker |
| Create | `tests/harness/test_run_registry.py` | `RunRegistry` unit tests |
| Create | `tests/harness/test_checkpoint.py` | Checkpoint factory tests |
| Modify | `pyproject.toml` | Add `langgraph-checkpoint-sqlite` and `pytest` |
| Modify | `workflows/hubspot_company_research/workflow.py` | `build_graph(checkpointer=)`, `run_workflow`, updated CLI |

---

## Task 1: Add dependencies and scaffold package structure

**Files:**
- Modify: `pyproject.toml`
- Create: `harness/__init__.py`, `tests/__init__.py`, `tests/harness/__init__.py`

- [ ] **Step 1: Add dependencies to pyproject.toml**

Edit `pyproject.toml` — add to the `dependencies` list:

```toml
[project]
name = "agent-harness"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "deepagents>=0.4.12",
    "hubspot>=0.1.14.dev0",
    "hubspot-api-client>=12.0.0",
    "langchain>=1.2.13",
    "langchain-openai>=1.1.12",
    "langchain-perplexity>=1.2.0",
    "langgraph-checkpoint-sqlite>=2.0.0",
    "python-docx>=1.2.0",
    "python-dotenv>=1.2.2",
    "pyyaml>=6.0.3",
    "tavily-python>=0.7.23",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.15.12",
]
```

- [ ] **Step 2: Sync dependencies**

```bash
uv sync
```

Expected: resolves and installs `langgraph-checkpoint-sqlite` and `pytest` with no errors.

- [ ] **Step 3: Create package and test scaffolding**

```bash
touch harness/__init__.py tests/__init__.py tests/harness/__init__.py
```

- [ ] **Step 4: Verify pytest is runnable**

```bash
uv run pytest --collect-only
```

Expected: `no tests ran` (0 items collected, no errors).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock harness/__init__.py tests/__init__.py tests/harness/__init__.py
git commit -m "chore: scaffold harness package and add langgraph-checkpoint-sqlite + pytest"
```

---

## Task 2: Implement RunRegistry (TDD)

**Files:**
- Create: `tests/harness/test_run_registry.py`
- Create: `harness/run_registry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/harness/test_run_registry.py`:

```python
import pytest
from harness.run_registry import COMPLETED, FAILED, PENDING, RUNNING, Run, RunRegistry


@pytest.fixture
def registry(tmp_path):
    return RunRegistry(tmp_path / "test.db")


def test_create_run_returns_pending_run(registry):
    run = registry.create_run("my_workflow", "subject-1", {"company_id": "123"})
    assert isinstance(run, Run)
    assert run.status == PENDING
    assert run.workflow == "my_workflow"
    assert run.subject == "subject-1"
    assert run.inputs == {"company_id": "123"}
    assert run.attempt == 1
    assert run.started_at is None
    assert run.outputs is None
    assert run.error is None
    assert len(run.run_id) == 36  # UUID4 format


def test_create_run_generates_unique_ids(registry):
    run_a = registry.create_run("wf", "s", {})
    run_b = registry.create_run("wf", "s", {})
    assert run_a.run_id != run_b.run_id


def test_mark_running_first_time_does_not_increment_attempt(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    updated = registry.get_run(run.run_id)
    assert updated.status == RUNNING
    assert updated.attempt == 1
    assert updated.started_at is not None


def test_mark_running_on_resume_increments_attempt_and_clears_error(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.fail_run(run.run_id, "timeout")
    registry.mark_running(run.run_id)  # resume
    updated = registry.get_run(run.run_id)
    assert updated.status == RUNNING
    assert updated.attempt == 2
    assert updated.error is None


def test_complete_run(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.complete_run(run.run_id, {"report": "text", "score": 87})
    updated = registry.get_run(run.run_id)
    assert updated.status == COMPLETED
    assert updated.outputs == {"report": "text", "score": 87}
    assert updated.completed_at is not None


def test_fail_run(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.fail_run(run.run_id, "API rate limit exceeded")
    updated = registry.get_run(run.run_id)
    assert updated.status == FAILED
    assert updated.error == "API rate limit exceeded"
    assert updated.completed_at is not None


def test_get_run_returns_none_for_unknown_id(registry):
    assert registry.get_run("00000000-0000-0000-0000-000000000000") is None


def test_list_runs_returns_all(registry):
    registry.create_run("wf_a", "s1", {})
    registry.create_run("wf_b", "s2", {})
    runs = registry.list_runs()
    assert len(runs) == 2


def test_list_runs_filters_by_workflow(registry):
    registry.create_run("wf_a", "s1", {})
    registry.create_run("wf_b", "s2", {})
    runs = registry.list_runs(workflow="wf_a")
    assert len(runs) == 1
    assert runs[0].workflow == "wf_a"


def test_list_runs_filters_by_status(registry):
    run = registry.create_run("wf", "s", {})
    registry.mark_running(run.run_id)
    registry.complete_run(run.run_id, {})
    registry.create_run("wf", "s2", {})  # PENDING
    completed = registry.list_runs(status=COMPLETED)
    assert len(completed) == 1
    assert completed[0].status == COMPLETED


def test_list_runs_ordered_newest_first(registry):
    registry.create_run("wf", "s1", {})
    registry.create_run("wf", "s2", {})
    runs = registry.list_runs()
    assert runs[0].created_at >= runs[1].created_at
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/harness/test_run_registry.py -v
```

Expected: `ImportError` — `harness.run_registry` does not exist yet.

- [ ] **Step 3: Implement harness/run_registry.py**

Create `harness/run_registry.py`:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/harness/test_run_registry.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add harness/run_registry.py tests/harness/test_run_registry.py
git commit -m "feat: implement RunRegistry with SQLite persistence"
```

---

## Task 3: Implement checkpoint factories (TDD)

**Files:**
- Create: `tests/harness/test_checkpoint.py`
- Create: `harness/checkpoint.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/harness/test_checkpoint.py`:

```python
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from harness.checkpoint import make_async_saver, make_sync_saver


def test_make_sync_saver_returns_sqlite_saver(tmp_path):
    saver = make_sync_saver(tmp_path / "cp.db")
    assert isinstance(saver, SqliteSaver)


def test_make_sync_saver_accepts_string_path(tmp_path):
    saver = make_sync_saver(str(tmp_path / "cp.db"))
    assert isinstance(saver, SqliteSaver)


def test_make_async_saver_returns_async_sqlite_saver(tmp_path):
    saver = make_async_saver(tmp_path / "cp.db")
    assert isinstance(saver, AsyncSqliteSaver)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/harness/test_checkpoint.py -v
```

Expected: `ImportError` — `harness.checkpoint` does not exist yet.

- [ ] **Step 3: Implement harness/checkpoint.py**

Create `harness/checkpoint.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def make_sync_saver(db_path: str | Path) -> SqliteSaver:
    """Return a ready-to-use synchronous LangGraph SQLite checkpointer.

    Uses a persistent connection with check_same_thread=False, suitable
    for single-process CLI use. Call saver.setup() is called internally
    to create the checkpoint tables on first use.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    saver = SqliteSaver(conn=conn)
    saver.setup()
    return saver


def make_async_saver(db_path: str | Path) -> AsyncSqliteSaver:
    """Return a ready-to-use async LangGraph SQLite checkpointer.

    Intended for FastAPI / async server contexts. Use as an async
    context manager or pass directly to build_graph(checkpointer=).
    """
    return AsyncSqliteSaver.from_conn_string(str(db_path))
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/harness/test_checkpoint.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all 14 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add harness/checkpoint.py tests/harness/test_checkpoint.py
git commit -m "feat: implement checkpoint saver factories"
```

---

## Task 4: Wire build_graph and run_workflow into workflow.py

**Files:**
- Modify: `workflows/hubspot_company_research/workflow.py`

The changes are: (1) `build_graph` passes `checkpointer` to `compile()`, (2) add `WORKFLOW_NAME`, `_OUTPUT_KEYS`, `run_workflow`, and `_print_runs` as module-level constants/functions.

- [ ] **Step 1: Update build_graph signature and compile call**

In `workflows/hubspot_company_research/workflow.py`, replace:

```python
def build_graph():
    builder = StateGraph(AgentState)
```

with:

```python
def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)
```

And replace:

```python
    return builder.compile()
```

with:

```python
    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 2: Add imports, constants, and helpers at module level**

After the existing imports block at the top of `workflow.py`, add:

```python
import os
import sys
```

After the `_has_gaps` function, add:

```python
WORKFLOW_NAME = "hubspot_company_research"

_OUTPUT_KEYS = (
    "report_markdown",
    "scoring_summary",
    "hubspot_update_status",
    "total_citations",
    "formatted_report_path",
)


def run_workflow(registry, graph, run_id: str, inputs: dict):
    registry.mark_running(run_id)
    try:
        state = graph.invoke(inputs, config={"configurable": {"thread_id": run_id}})
        outputs = {k: state.get(k) for k in _OUTPUT_KEYS}
        registry.complete_run(run_id, outputs)
        return state
    except Exception as exc:
        registry.fail_run(run_id, str(exc))
        raise


def _print_runs(runs: list) -> None:
    if not runs:
        print("No runs found.")
        return
    header = f"{'RUN_ID':<36}  {'SUBJECT':<14}  {'STATUS':<10}  {'ATT':>3}  {'CREATED':<26}  ERROR"
    print(header)
    print("-" * (len(header) + 10))
    for r in runs:
        error = (r.error or "")[:50]
        print(
            f"{r.run_id:<36}  {r.subject:<14}  {r.status:<10}  {r.attempt:>3}"
            f"  {r.created_at:<26}  {error}"
        )
```

- [ ] **Step 3: Verify the graph still builds without a checkpointer**

```bash
python -c "from workflows.hubspot_company_research.workflow import build_graph; g = build_graph(); print('OK')"
```

Expected: prints `OK` with no errors.

- [ ] **Step 4: Commit**

```bash
git add workflows/hubspot_company_research/workflow.py
git commit -m "feat: add run_workflow helper and checkpointer injection to build_graph"
```

---

## Task 5: Update CLI with --resume and --list-runs

**Files:**
- Modify: `workflows/hubspot_company_research/workflow.py`

- [ ] **Step 1: Replace _parse_args and the __main__ block**

Replace the existing `_parse_args` function and `if __name__ == "__main__":` block with:

```python
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the HubSpot Company Research workflow")
    parser.add_argument("company_id", nargs="?", help="HubSpot company ID (fresh run)")
    parser.add_argument("--resume", metavar="RUN_ID", help="Resume a FAILED or RUNNING run by ID")
    parser.add_argument("--list-runs", action="store_true", help="List recent runs for this workflow")
    parser.add_argument("--status", help="Filter --list-runs by status: PENDING, RUNNING, COMPLETED, FAILED")
    parser.add_argument(
        "--property-value",
        default="Requested",
        help="Simulated value of intelligence_report_status (default: 'Requested')",
    )
    return parser.parse_args()


if __name__ == "__main__":
    from harness.checkpoint import make_sync_saver
    from harness.run_registry import FAILED, RUNNING, RunRegistry

    args = _parse_args()

    db_path = Path(os.getenv("RUNS_DB_PATH", "output/runs.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    registry = RunRegistry(db_path)

    if args.list_runs:
        runs = registry.list_runs(workflow=WORKFLOW_NAME, status=args.status or None)
        _print_runs(runs)
        sys.exit(0)

    if args.resume:
        run = registry.get_run(args.resume)
        if not run:
            print(f"Run not found: {args.resume}", file=sys.stderr)
            sys.exit(1)
        if run.status not in {FAILED, RUNNING}:
            print(
                f"Cannot resume: status is '{run.status}'. Only FAILED or RUNNING runs are resumable.",
                file=sys.stderr,
            )
            sys.exit(1)
        saver = make_sync_saver(db_path)
        graph = build_graph(checkpointer=saver)
        final_state = run_workflow(registry, graph, args.resume, run.inputs)
        print(f"Run {args.resume} completed.")
        print(f"HubSpot update status: {final_state.get('hubspot_update_status') or 'skipped'}")
        sys.exit(0)

    if not args.company_id:
        print(
            "Error: provide a company_id for a fresh run, --resume RUN_ID, or --list-runs.",
            file=sys.stderr,
        )
        sys.exit(1)

    run_dir = Path("output") / dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    inputs = {
        "company_id": args.company_id,
        "property_value": args.property_value,
        "output_dir": str(run_dir),
    }
    run = registry.create_run(WORKFLOW_NAME, args.company_id, inputs)
    saver = make_sync_saver(db_path)
    graph = build_graph(checkpointer=saver)
    final_state = run_workflow(registry, graph, run.run_id, inputs)
    print(f"Run {run.run_id} complete. Output written to: {run_dir}")
    print(f"HubSpot update status: {final_state.get('hubspot_update_status') or 'skipped'}")
```

- [ ] **Step 2: Verify --list-runs works against an empty DB**

```bash
python workflows/hubspot_company_research/workflow.py --list-runs
```

Expected: prints `No runs found.` with no errors.

- [ ] **Step 3: Verify --resume rejects unknown run ID**

```bash
python workflows/hubspot_company_research/workflow.py --resume 00000000-0000-0000-0000-000000000000
```

Expected: prints `Run not found: 00000000-...` and exits with code 1.

- [ ] **Step 4: Verify --help output**

```bash
python workflows/hubspot_company_research/workflow.py --help
```

Expected: shows `company_id`, `--resume`, `--list-runs`, `--status`, `--property-value` in the help text.

- [ ] **Step 5: Commit**

```bash
git add workflows/hubspot_company_research/workflow.py
git commit -m "feat: add --resume and --list-runs CLI flags with run registry integration"
```

---

## Task 6: Write harness/README.md

**Files:**
- Create: `harness/README.md`

- [ ] **Step 1: Write the README**

Create `harness/README.md`:

```markdown
# harness

General-purpose utilities for LangGraph workflow persistence and fault tolerance.

## What it provides

- **`RunRegistry`** — tracks every workflow run (status, inputs, outputs, error) in a SQLite `runs` table
- **`make_sync_saver`** / **`make_async_saver`** — LangGraph checkpointer factories that write to the same SQLite file, enabling automatic state snapshots after every graph node

Both components write to the same SQLite file but to independent table namespaces — they never interfere.

## Setup

Install the LangGraph SQLite checkpointer (already in `pyproject.toml`):

```bash
uv sync
```

The default DB file is `output/runs.db`. Override with the `RUNS_DB_PATH` env var:

```bash
export RUNS_DB_PATH=/path/to/your/runs.db
```

## CLI — hubspot_company_research

```bash
# Fresh run
uv run python workflows/hubspot_company_research/workflow.py <company_id>

# List all runs for this workflow
uv run python workflows/hubspot_company_research/workflow.py --list-runs

# Filter by status (PENDING, RUNNING, COMPLETED, FAILED)
uv run python workflows/hubspot_company_research/workflow.py --list-runs --status FAILED

# Resume a failed or interrupted run — replays only incomplete nodes
uv run python workflows/hubspot_company_research/workflow.py --resume <run-id>
```

## Resume flow

When a run fails (API error, timeout, process crash):

1. Find the failed run:
   ```bash
   python workflows/hubspot_company_research/workflow.py --list-runs --status FAILED
   ```
2. Copy the `RUN_ID` from the output.
3. Resume:
   ```bash
   python workflows/hubspot_company_research/workflow.py --resume <run-id>
   ```

LangGraph restores state from the last successful node checkpoint. Only incomplete nodes re-execute. Already-completed LLM calls are not re-charged.

## Wiring a new workflow

**1. Accept an injected checkpointer in `build_graph`:**

```python
from langgraph.graph import StateGraph, END, START

def build_graph(checkpointer=None):
    builder = StateGraph(MyState)
    # ... add_node / add_edge calls ...
    return builder.compile(checkpointer=checkpointer)
```

**2. Define output keys and the run_workflow wrapper:**

```python
from harness.run_registry import RunRegistry

_OUTPUT_KEYS = ("field_a", "field_b")  # state keys worth recording on success

def run_workflow(registry: RunRegistry, graph, run_id: str, inputs: dict):
    registry.mark_running(run_id)
    try:
        state = graph.invoke(inputs, config={"configurable": {"thread_id": run_id}})
        registry.complete_run(run_id, {k: state.get(k) for k in _OUTPUT_KEYS})
        return state
    except Exception as exc:
        registry.fail_run(run_id, str(exc))
        raise
```

**3. Create a run and invoke:**

```python
import os
from pathlib import Path
from harness.checkpoint import make_sync_saver

db_path = Path(os.getenv("RUNS_DB_PATH", "output/runs.db"))
db_path.parent.mkdir(parents=True, exist_ok=True)

registry = RunRegistry(db_path)
saver = make_sync_saver(db_path)
graph = build_graph(checkpointer=saver)

run = registry.create_run("my_workflow", subject_id, inputs)
run_workflow(registry, graph, run.run_id, inputs)
```

**4. For async (FastAPI / webhook server), swap the saver:**

```python
from harness.checkpoint import make_async_saver

saver = make_async_saver(db_path)
graph = build_graph(checkpointer=saver)
# use graph.ainvoke(...) instead of graph.invoke(...)
```

## Run status reference

| Status | Meaning | Resumable? |
|---|---|---|
| `PENDING` | Created, not yet started | No |
| `RUNNING` | Currently executing | Yes (if process died) |
| `COMPLETED` | Finished successfully | No |
| `FAILED` | Raised an exception | Yes |
```

- [ ] **Step 2: Commit**

```bash
git add harness/README.md
git commit -m "docs: add harness README with setup, CLI, and wiring guide"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| Resumable runs | Task 4 `run_workflow` + Task 5 `--resume` |
| Full fault tolerance (API + crash) | LangGraph checkpointer (Task 3) + `fail_run` on exception (Task 4) |
| Run lifecycle tracking | Task 2 `RunRegistry` |
| General-purpose — not coupled to one workflow | `harness/` package with no workflow imports; `WORKFLOW_NAME` in workflow.py |
| CLI resumption `--resume` | Task 5 |
| User documentation | Task 6 `harness/README.md` |

**No placeholders found.** All steps contain complete code.

**Type consistency:** `RunRegistry`, `Run`, `PENDING/RUNNING/COMPLETED/FAILED` defined in Task 2 and referenced consistently in Tasks 4 and 5. `make_sync_saver` / `make_async_saver` defined in Task 3 and imported in Tasks 4 and 5. No naming drift.
