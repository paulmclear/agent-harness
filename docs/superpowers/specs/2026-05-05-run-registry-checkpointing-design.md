# Run Registry & Checkpointing — Design Spec

**Date:** 2026-05-05  
**Status:** Approved  
**Scope:** General-purpose harness utility; initial integration with `hubspot_company_research` workflow

---

## Problem

LangGraph workflows in this repo run long chains of expensive LLM calls (13+ per run) with no persistence. A mid-run API error or process crash loses all work. There is no way to resume, no record of what ran, and no visibility into run status.

---

## Goals

1. Resumable runs — resume from the last successful node after any failure
2. Full fault tolerance — survives API errors, process crashes, and machine restarts
3. Run lifecycle tracking — status, inputs, outputs, and error recorded per run
4. General-purpose — not coupled to any single workflow
5. CLI resumption — `--resume <run-id>` replays a failed run without re-spending completed nodes
6. User documentation — README covering setup, CLI usage, resume flow, and how to wire a new workflow into the harness

---

## Non-Goals

- Automatic retry (out of scope; manual replay only)
- Distributed / multi-process checkpointing
- Web UI for run status
- Modifying any workflow other than `hubspot_company_research` in this iteration

---

## Architecture

### New package: `harness/`

```
harness/
  __init__.py
  run_registry.py    — RunRegistry class, Run dataclass, status constants
  checkpoint.py      — sync and async SQLite saver factories
```

A single SQLite file (`output/runs.db` by default) holds both:
- LangGraph's internal checkpoint tables (written by `SqliteSaver` / `AsyncSqliteSaver`)
- The `runs` job-registry table (written by `RunRegistry`)

The two table namespaces never overlap. Callers pass the same `db_path` to both.

### Lifecycle

```
Fresh run:
  create_run(workflow, subject, inputs)  → PENDING, generates UUID run_id
  mark_running(run_id)                   → RUNNING
  graph.invoke(..., thread_id=run_id)    ← LangGraph checkpoints after every node
  complete_run(run_id, outputs)          → COMPLETED

Resume:
  get_run(run_id)                        validates status is FAILED or RUNNING
  mark_running(run_id), bumps attempt
  graph.invoke(same thread_id)           LangGraph skips already-completed nodes
  complete_run / fail_run
```

---

## Data Model

### `runs` table

| Column | Type | Notes |
|---|---|---|
| `run_id` | TEXT PK | UUID4; doubles as LangGraph `thread_id` |
| `workflow` | TEXT | e.g. `"hubspot_company_research"` — namespaces runs |
| `subject` | TEXT | Human-readable identifier for what the run is about (caller-defined: `company_id`, date range, etc.) |
| `status` | TEXT | `PENDING` / `RUNNING` / `COMPLETED` / `FAILED` |
| `created_at` | TEXT | ISO-8601 UTC |
| `started_at` | TEXT | nullable; set on first invoke or resume |
| `completed_at` | TEXT | nullable |
| `attempt` | INTEGER | starts at 1; increments on each resume |
| `inputs_json` | TEXT | JSON snapshot of initial invoke inputs |
| `outputs_json` | TEXT | nullable; JSON snapshot of caller-defined output keys on success |
| `error` | TEXT | nullable; exception message on failure |

### Status transitions

```
create_run()    → PENDING
mark_running()  → RUNNING
complete_run()  → COMPLETED
fail_run()      → FAILED    (resumable via --resume)
```

### DB path

Default: `output/runs.db`. Overridable via `RUNS_DB_PATH` env var.

---

## `harness/run_registry.py`

```python
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

class RunRegistry:
    def __init__(self, db_path: str | Path) -> None
    def create_run(self, workflow: str, subject: str, inputs: dict) -> Run
    def mark_running(self, run_id: str) -> None
    def complete_run(self, run_id: str, outputs: dict) -> None
    def fail_run(self, run_id: str, error: str) -> None
    def get_run(self, run_id: str) -> Run | None
    def list_runs(self, workflow: str | None = None, status: str | None = None) -> list[Run]
```

`RunRegistry.__init__` creates the `runs` table if it does not exist. All methods are synchronous; the SQLite connection is managed per-call (thread-safe for CLI use; the server path uses a dedicated connection or runs in a single-threaded event loop context).

---

## `harness/checkpoint.py`

```python
def make_sync_saver(db_path: str | Path) -> SqliteSaver
def make_async_saver(db_path: str | Path) -> AsyncSqliteSaver
```

Both functions open the SQLite file at `db_path` and return a ready-to-use LangGraph checkpointer. The server path swaps `make_sync_saver` for `make_async_saver` with no other changes.

---

## Workflow Integration — `hubspot_company_research`

### `build_graph` signature change

```python
def build_graph(checkpointer=None) -> CompiledGraph
```

The checkpointer is injected at call time rather than hardcoded, keeping `build_graph` testable without a DB.

### Run lifecycle wrapper

```python
_OUTPUT_KEYS = (
    "report_markdown",
    "scoring_summary",
    "hubspot_update_status",
    "total_citations",
    "formatted_report_path",
)

def run_workflow(registry: RunRegistry, graph, run_id: str, inputs: dict) -> AgentState:
    registry.mark_running(run_id)
    try:
        state = graph.invoke(inputs, config={"configurable": {"thread_id": run_id}})
        outputs = {k: state.get(k) for k in _OUTPUT_KEYS}
        registry.complete_run(run_id, outputs)
        return state
    except Exception as exc:
        registry.fail_run(run_id, str(exc))
        raise
```

### Updated CLI flags

```
python workflow.py <company_id>                  # fresh run
python workflow.py --resume <run-id>             # replay from last checkpoint
python workflow.py --list-runs                   # recent runs, all statuses
python workflow.py --list-runs --status FAILED   # filter by status
```

`--resume` validates the run exists and has status `FAILED` or `RUNNING` before invoking. The CLI loads `run.inputs` from the registry and passes it to `run_workflow` — the caller does not need to repeat `company_id` or any other input.

---

## Dependencies

- `langgraph-checkpoint-sqlite` — adds `SqliteSaver` and `AsyncSqliteSaver`
- Standard library `sqlite3`, `uuid`, `datetime` — no additional deps for `RunRegistry`

---

## What Is Not Changed

- `AgentState` — no new fields; run metadata lives entirely in `harness/`, not in graph state
- Node implementations — no node is aware of the registry or checkpointing
- Other workflows (`lead_gen_fcc_intel`) — not modified in this iteration, but can adopt the same pattern by importing from `harness/`
