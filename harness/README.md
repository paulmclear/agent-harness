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
uv run python -m workflows.hubspot_company_research.workflow <company_id>

# List all runs for this workflow
uv run python -m workflows.hubspot_company_research.workflow --list-runs

# Filter by status (PENDING, RUNNING, COMPLETED, FAILED)
uv run python -m workflows.hubspot_company_research.workflow --list-runs --status FAILED

# Resume a failed or interrupted run — replays only incomplete nodes
uv run python -m workflows.hubspot_company_research.workflow --resume <run-id>
```

## Resume flow

When a run fails (API error, timeout, process crash):

1. Find the failed run:
   ```bash
   uv run python -m workflows.hubspot_company_research.workflow --list-runs --status FAILED
   ```
2. Copy the `RUN_ID` from the output.
3. Resume:
   ```bash
   uv run python -m workflows.hubspot_company_research.workflow --resume <run-id>
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
