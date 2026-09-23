# Memory & State Patterns — Checkpointers, State Schema, Context Compaction

Persisting state, managing context budgets, and long-term memory.

## State Schema with Reducers

Reducers define how concurrent or sequential updates merge into state. Without a reducer, the last write wins.

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
import operator

def merge_dicts(existing: dict, new: dict) -> dict:
    """Custom reducer — deep merge dictionaries."""
    merged = {**existing}
    for k, v in new.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = merge_dicts(merged[k], v)
        else:
            merged[k] = v
    return merged

class HarnessState(TypedDict):
    messages: Annotated[list, add_messages]       # Built-in message reducer
    results: Annotated[list, operator.add]         # Append-only list
    metadata: Annotated[dict, merge_dicts]         # Deep-merge dict
    iteration_count: int                           # Last-write-wins (no reducer)
```

**When to use each reducer type:**
- `add_messages` — Chat history. Handles message deduplication and updates by ID.
- `operator.add` — Collecting results from parallel nodes (fan-in). Each node appends its results.
- Custom `merge_dicts` — When multiple nodes update different keys of the same dict.
- No reducer (last-write-wins) — Simple counters, phase markers, flags.

## Checkpointing — Persist and Resume

Save graph state so harnesses can resume after failure, human approval, or server restart.

### Development — SQLite

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)

    # Run with a thread ID — enables resume
    config = {"configurable": {"thread_id": "harness-run-001"}}
    result = graph.invoke(initial_state, config)
```

### Production — PostgreSQL

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string(
    "postgresql://user:pass@host/db"
) as checkpointer:
    checkpointer.setup()  # Create tables on first run
    graph = builder.compile(checkpointer=checkpointer)
```

### Resume from Failure

```python
# Check what state we're in
state = graph.get_state(config)
print(f"Resuming from phase: {state.values['phase']}")

# Resume — pass None to continue from last checkpoint
result = graph.invoke(None, config)
```

### When You Need a Checkpointer

- **Human-in-the-loop** — `interrupt_before` / `interrupt_after` require a checkpointer. Without one, the graph can't pause and resume.
- **Long-running harnesses** — If a run takes hours, checkpoint so it survives server restarts.
- **Debugging** — Time-travel debugging: inspect state at any checkpoint.
- **Multi-user production** — Each thread_id is an independent run with its own state history.

## Context Compaction (Message Trimming)

Keep the context window lean. Critical for long-running agents that accumulate many tool calls.

### Strategy 1: Token-based Trimming

Keep the most recent N tokens of conversation. Simple and effective.

```python
from langchain_core.messages import trim_messages
from langchain_anthropic import ChatAnthropic

trimmer = trim_messages(
    max_tokens=8000,
    strategy="last",           # Keep most recent messages
    token_counter=ChatAnthropic(model="claude-sonnet-4-20250514"),
    include_system=True,       # Always keep the system prompt
    start_on="human",          # Ensure we start on a human turn
)

def agent_with_trimming(state: MessagesState) -> dict:
    trimmed = trimmer.invoke(state["messages"])
    response = model.invoke(trimmed)
    return {"messages": [response]}
```

### Strategy 2: Summarise and Reset

Compress history into a summary, keep only the last few messages for continuity. Better for very long sessions.

```python
from langchain_core.messages import SystemMessage

def maybe_compact_context(state: HarnessState) -> dict:
    messages = state["messages"]
    if len(messages) > 50:  # Threshold
        summary_prompt = f"Summarise this conversation concisely:\n{messages}"
        summary = model.invoke(summary_prompt)
        return {
            "messages": [
                SystemMessage(content=f"Previous context summary: {summary.content}"),
                *messages[-5:]  # Keep last 5 messages for continuity
            ]
        }
    return {}  # No compaction needed
```

### Strategy 3: File-based Context Offloading

Save verbose outputs to files. Provide the agent with summaries and file navigation tools.

```python
@tool
def save_to_workspace(filename: str, content: str) -> str:
    """Save content to the workspace. Returns a summary for the agent."""
    path = f"./workspace/{filename}"
    with open(path, "w") as f:
        f.write(content)
    # Return a brief summary, not the full content
    return f"Saved {len(content)} chars to {path}. First 200 chars: {content[:200]}..."

@tool
def read_from_workspace(filename: str) -> str:
    """Read a file from the workspace when you need the full content."""
    path = f"./workspace/{filename}"
    with open(path) as f:
        return f.read()
```

### Choosing a Compaction Strategy

| Strategy | Best for | Trade-off |
|---|---|---|
| Token trimming | Moderate conversations (< 100 messages) | Loses old context entirely |
| Summarise-and-reset | Very long sessions (hours of work) | Summary may lose details |
| File-based offloading | Verbose tool outputs (API responses, logs) | Agent must know to check files |
| Context resets (fresh window) | Multi-sprint work, Initialiser/Coder pattern | Requires progress tracking files |

## Long-term Memory — Vector Store

Persist knowledge across sessions.

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Initialise vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
memory_store = Chroma(
    collection_name="agent_memory",
    embedding_function=embeddings,
    persist_directory="./memory_db"
)

# Save a memory after each harness run
def save_run_memory(state: HarnessState):
    memory_store.add_texts(
        texts=[f"Task: {state['task']}\nOutcome: {state['final_output']}"],
        metadatas=[{
            "run_id": state["run_id"],
            "timestamp": datetime.now().isoformat(),
        }]
    )

# Recall relevant past runs
def recall_similar_tasks(query: str, k: int = 3) -> list:
    return memory_store.similarity_search(query, k=k)
```

## Progress Tracking Files (Initialiser/Coder Pattern)

For multi-sprint work where each sub-agent or sprint reads what's been done and picks up the next task.

```python
import json

PROGRESS_FILE = "./workspace/progress.json"

def read_progress() -> dict:
    """Read current progress state."""
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"features": [], "completed": [], "current": None}

def update_progress(feature: str, status: str):
    """Update progress tracking after completing a feature."""
    progress = read_progress()
    if status == "complete":
        progress["completed"].append(feature)
        # Set next feature as current
        remaining = [f for f in progress["features"] if f not in progress["completed"]]
        progress["current"] = remaining[0] if remaining else None
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)
```

This pattern enables context resets: each new agent session reads the progress file to know where to pick up, without needing the full conversation history from previous sessions.
